# Multivisor repository guide

This file is the operational contract for both human contributors and coding
agents. It applies to the entire repository. Keep it synchronized with the
actual setup, test, and branch workflow whenever those change.

## Product and architecture

Multivisor is a centralized UI and CLI for one or more Supervisor instances.
The main runtime paths are:

- `multivisor/server/`: Flask/gevent web server and packaged Vue application.
- `multivisor/client/`: interactive HTTP/SSE CLI client.
- `multivisor/rpc.py`: optional in-process Supervisor RPC interface.
- `multivisor/server/rpc.py`: optional Supervisor event-listener RPC bridge.
- `multivisor/multivisor.py`: web-side model and ZeroRPC client.
- `src/`: Vue frontend source.
- `multivisor/server/dist/`: committed frontend build used by source checkouts
  and Docker. Do not hand-edit generated files here.
- `tests/` and `multivisor/**/tests/`: integration and unit tests.
- `docker/`: Docker demo/runtime packaging.

The web process and Supervisor process may run in different Python
environments or on different hosts. Supervisor is therefore a peer runtime for
the RPC component, not a general dependency of the web or CLI component.

## Branch workflow

Use Git Flow naming and target rules:

- `main`: group-approved operational history; no package publication required.
- `develop`: integration branch for the next release.
- `feature/*`: user-visible capabilities; merge into `develop`.
- `fix/*`: defect fixes; merge into `develop` unless it is a production hotfix.
- `refactor/*`: structural, packaging, dependency, or tooling improvements;
  merge into `develop`.
- `release/*`: operational release preparation; merge into `main` and back
  into `develop`.
- `hotfix/*`: urgent production fixes; merge into `main` and `develop`.
- `upstream_develop`: local synchronization branch tracking
  `upstream/develop`; do not develop directly on it.

Do not mix unrelated work into an active branch. Preserve user changes in a
dirty worktree and never rewrite shared history without explicit authorization.

## Python runtime policy

- Package floor: CPython 3.12.
- Default local and Docker runtime: CPython 3.14 with the normal GIL.
- Compatibility lanes: CPython 3.12, 3.13, and 3.14.
- Free-threaded CPython (`3.14t`) is unsupported because gevent/greenlet do not
  support that execution mode.
- `.python-version`, `requires-python`, classifiers, CI, Docker images, and the
  runtime policy in `README.md` and `PACKAGING.md` must agree.

The Multivisor RPC package and adapter code support CPython 3.12–3.14.
Supervisor is an independently managed peer runtime: public extras do not
install, upgrade, constrain, or document its interpreter/dependency policy.
Install the adapter into the environment selected by the host administrator.
The central web server and CLI can use a separate Python environment on the
same or another machine. See `PACKAGING.md` for the adapter installation
boundary.

## Initial setup

Install uv, then from the repository root run:

```console
uv python install 3.12 3.13 3.14
uv sync --frozen --extra all
```

The committed `uv.lock` is authoritative. If `pyproject.toml` dependencies or
the supported Python range change, regenerate the lock with `uv lock` and
commit both files together.

For frontend work:

```console
npm ci
npm run lint
npm run build
```

Commit frontend source, `package-lock.json`, and the regenerated
`multivisor/server/dist/` in the same change.

## Required checks

Run the smallest focused test while iterating, then the checks appropriate to
the final diff.

### Python source or dependency changes

```console
uv lock --check
uv run --frozen ruff check .
uv run --frozen pytest -q
```

For runtime-version work, test the central web/CLI package on every supported
interpreter without replacing an environment that may be running the local web
server:

```console
uv run --isolated --python 3.12 --extra all --frozen ruff check .
uv run --isolated --python 3.12 --extra all --frozen pytest -q
uv run --isolated --python 3.13 --extra all --frozen ruff check .
uv run --isolated --python 3.13 --extra all --frozen pytest -q
uv run --isolated --python 3.14 --extra all --frozen ruff check .
uv run --isolated --python 3.14 --extra all --frozen pytest -q
```

Run real Supervisor/RPC integration with a separately managed peer environment
for the supported adapter versions, using `--group rpc-test` where applicable.
Keep cross-runtime central-to-peer coverage. RPC lanes must fail, rather than
skip, if the required peer or adapter executable is missing.

### Frontend changes

```console
npm ci
npm run lint
npm run build
git diff --check
```

Then run the Python tests because the built UI is package data.

### Docker changes

```console
docker build -f docker/Dockerfile -t multivisor:local .
docker run --rm multivisor:local multivisor --help
```

Verify the three-Supervisor demo topology, a real RPC/event-listener connection,
and an HTTP route when runtime scripts, server behavior, or packaged assets
change. Use disposable names, an isolated network, and an unused host port;
never reuse a user's production container name or port.

## Code and compatibility rules

- Write syntax accepted by the declared Python floor (currently 3.12).
- Prefer current Python idioms; `ruff`'s configured `UP` rules are enforced.
- Do not add Python 2 compatibility branches, `u` string prefixes,
  `class X(object)`, or two-argument `super()` calls.
- Use `logging.warning`, not deprecated `logging.warn`.
- Keep network protocols stable unless the task explicitly changes them.
- Supervisor numeric wire values used by the independent web process live in
  `multivisor/supervisor_protocol.py` and must be backed by focused tests.
- Treat ZeroRPC and Supervisor as compatibility-sensitive legacy dependencies.
  Exercise a real round trip for changes that touch RPC behavior.
- Do not silently broaden exception handling or change process-state semantics
  as part of mechanical modernization.
- Keep public CLI flags, INI keys, REST paths, SSE payloads, and Vue behavior
  backward compatible unless a documented migration is intentional.

## Package and installation rules

- Keep `pyproject.toml`, the build backend, and console-script declarations as
  a normal installable package. Operational projects install an immutable Git
  tag with a direct requirement such as
  `multivisor[web] @ git+https://github.com/SinclairQuantumLab/multivisor.git@<tag>`.
  Each command requires its corresponding extra; RPC adapters need a Supervisor
  peer.
- Release tags are created only from `main` after the required checks pass.
  Development and integration branches must never be used as production Git
  dependencies. A release may build a wheel/sdist for validation or explicit
  publication; never commit those artifacts.
- Retain explicit frontend package data and test-package exclusions. The
  committed `multivisor/server/dist/` must contain index.html, favicon.ico,
  and referenced assets. Do not hand-edit generated files.
- Installer-generated intermediate wheels/caches are implementation details,
  not managed release artifacts.
- Docker uses locked dependencies and a non-editable install because only its
  environment is copied to the runtime image. Keep its explicit docker extra.
- Use uv and npm as the maintained environment tools.
- Keep operational projects separate from development and stop services before
  changing their locked package revision or environment. See `PACKAGING.md`.
- Never commit environments, distribution artifacts, caches, logs, credentials,
  or local Supervisor state.

## Documentation and change ledger

Follow `.agents/README.md`. Update current usage and operational documents
when behavior changes. Routine maintenance needs a clear commit/PR description
and relevant verification, not a separate changelog entry.

The README initial-change summary records the fork's foundation; do not grow
it with every fix. Preserve existing engineering history. Add migration notes
only for operator action or significant architectural/runtime decisions, with
the rationale, required steps, actual verification, and known limitations.
Do not require exhaustive file inventories or failed-iteration diaries.

## Definition of done

A change is complete only when the implementation, focused tests, full relevant
test matrix, documentation, and clean tracked `git status` agree. Preserve
unrelated user files. For documentation/workflow-only changes, check links,
command validity, and the affected workflow; do not repeat runtime matrices
unless the change affects them. Report known platform gaps honestly.
