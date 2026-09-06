# Multivisor repository guide

This file is the operational contract for both human contributors and coding
agents. It applies to the entire repository. Keep it synchronized with the
actual build, test, packaging, and branch workflow whenever those change.

## Product and architecture

Multivisor is a centralized UI and CLI for one or more Supervisor instances.
The main runtime paths are:

- `multivisor/server/`: Flask/gevent web server and packaged Vue application.
- `multivisor/client/`: interactive HTTP/SSE CLI client.
- `multivisor/rpc.py`: optional in-process Supervisor RPC interface.
- `multivisor/server/rpc.py`: optional Supervisor event-listener RPC bridge.
- `multivisor/multivisor.py`: web-side model and ZeroRPC client.
- `src/`: Vue frontend source.
- `multivisor/server/dist/`: committed frontend build consumed by wheels and
  direct Git installs. Do not hand-edit generated files here.
- `tests/` and `multivisor/**/tests/`: integration and unit tests.
- `docker/`: Docker demo/runtime packaging.

The web process and Supervisor process may run in different Python
environments or on different hosts. Supervisor is therefore a peer runtime for
the RPC component, not a general dependency of the web or CLI component.

## Branch workflow

Use Git Flow naming and target rules:

- `main`: released/stable history.
- `develop`: integration branch for the next release.
- `feature/*`: user-visible capabilities; merge into `develop`.
- `fix/*`: defect fixes; merge into `develop` unless it is a production hotfix.
- `refactor/*`: structural, packaging, dependency, or tooling improvements;
  merge into `develop`.
- `release/*`: release preparation; merge into `main` and back into `develop`.
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
  runtime policy in `.agents/CHANGELOG.md` must agree.

Windows caveat: released `supervisor-win 4.7.0` constrains `pywin32` to
`>228,<=306`, whose wheels stop at CPython 3.12. Keep a Windows Supervisor/RPC
host on CPython 3.12; do not override that upstream dependency bound. The
central web server and CLI can run on CPython 3.14 on the same or another
machine. Both sides install the same Multivisor wheel because its Python floor
is 3.12; only their selected extras and peer runtimes differ. See
`.agents/CHANGELOG.md` for the exact topology, reasoning, and commands.

Supported RPC peer runtimes are Supervisor 4.3.0 or newer on Unix and
`supervisor-win 4.7.0` on Windows. Public extras do not install or upgrade this
peer; keep the RPC adapter in the same environment as the selected Supervisor.

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
uv build --no-sources
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

Run Supervisor/RPC integration on Unix 3.12, 3.13, and 3.14 by adding
`--group rpc-test`. On Windows, run that group only on 3.12. Also preserve the
CI cross-runtime lanes in which Python 3.13 and 3.14 central processes call a
Python 3.12 `supervisor-win` RPC host. RPC lanes must fail, rather than skip, if
the required Supervisor or adapter executable is missing.

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

## Packaging rules

- `uv build --no-sources` must succeed; this proves the package does not depend
  on uv-only source substitutions.
- Wheels must include `multivisor/server/dist/index.html`, `favicon.ico`, and
  every referenced asset.
- Wheels must exclude `multivisor.tests` and `multivisor.server.tests`. Keep
  `include-package-data = false` and declare runtime web assets explicitly so
  setuptools-scm cannot reintroduce tracked test files as package data.
- The project publishes one pure-Python distribution for 3.12+. Wheel tags and
  `Requires-Python` select compatible files; environment markers select
  platform dependencies. This is package metadata, not a GitHub repository
  setting.
- Wheels and direct Git installs expose `multivisor`, `multivisor-rpc`, and
  `multivisor-cli`. Each command still requires its corresponding extra, and
  both RPC adapters require an existing Supervisor peer runtime.
- Docker builds use `uv sync --frozen` and the locked `docker` extra so the
  Supervisor demo runtime is explicit and reproducible.
- Never commit virtual environments, caches, logs, or local Supervisor state.

## Documentation and change ledger

`.agents/README.md` defines the maintained documentation layout.
`.agents/CHANGELOG.md` is the reproducible engineering ledger. For every
material runtime, packaging, dependency, or workflow change:

1. Record the starting state and exact target.
2. Explain why the change is necessary and list known constraints.
3. List every changed file and the semantic effect.
4. Include copy-pasteable migration and verification commands.
5. Record actual results, failures encountered, and remaining limitations.
6. State structural, functional, and visual impact explicitly.

Do not mark a ledger entry complete until its documented checks have actually
passed. If reality and documentation disagree, fix both in the same commit.

## Definition of done

A change is complete only when the implementation, focused tests, full relevant
test matrix, package build, documentation, and clean `git status` agree. Report
known platform gaps rather than hiding them behind a broad support claim.
