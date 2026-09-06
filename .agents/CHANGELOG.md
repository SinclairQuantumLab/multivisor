# Engineering change ledger

This file preserves the initial engineering history and occasional substantial
migrations. Current policy lives in AGENTS.md and PACKAGING.md; older entries
below describe historical workflows, including superseded wheel-build steps.
Routine maintenance does not require another ledger entry.

## 2026-09-06 — Git-package deployment boundary

### Objective

Replace editable source-checkout operation with package installation from an
immutable Git release tag. Keep application development in this repository and
move group configuration, service definitions, and deployment locks to
`SinclairQuantumLab/multivisor-web`.

### Starting state and target

The preceding source-checkout policy required operators to clone this
repository and run `uv sync` in place. The target is an operational project
whose `pyproject.toml` contains a direct Git requirement such as:

```console
uv add "multivisor[web,cli] @ git+https://github.com/SinclairQuantumLab/multivisor.git@<release-tag>"
uv sync --frozen
```

The tag must be immutable and created from `main` only after required checks.
`develop` and work branches may be installed solely for disposable integration
tests. A direct Git reference cannot choose an older compatible release when
the selected revision's `Requires-Python` excludes the active interpreter.

### Files and effects

- `README.md`: replaces the operational checkout quick start with a
  `multivisor-web` Git-dependency workflow and documents tag-based updates.
- `PACKAGING.md`: documents central and RPC-host installation, lockfile update,
  rollback, and release build boundaries for direct Git dependencies.
- `AGENTS.md` and `.agents/README.md`: make release tags and package metadata,
  rather than editable checkout operation, the maintained contributor policy.
- `SinclairQuantumLab/multivisor-web` receives the corresponding deployment
  dependency and lockfile on its own `refactor/git-package-deployment` branch.

### Constraints and impact

This does not require publishing to PyPI or committing wheels. `uv` builds the
normal package from the selected Git revision; release builds remain useful for
validation and optional future publication. The change is structural and
operational only: no REST, SSE, RPC, frontend, or visible UI behavior changes.

### Verification

| Check | Result |
| --- | --- |
| `uv lock --check` in this repository | Passed on CPython 3.14.3 |
| `uv build --no-sources` | Passed; built a source distribution and pure-Python wheel without committing either artifact |
| Downstream Git resolution | `multivisor-web` locked `refactor/git-package-deployment` to commit `3f2caaf22b0241c0e62cb6f9d92251d968e88ace` |
| Downstream sync and command smoke tests | `uv sync --frozen`, `multivisor --help`, and `multivisor-cli --help` passed on CPython 3.14.3 |
| `git diff --check` | Passed in both repositories |

## 2026-09-06 — Source-checkout maintenance baseline

Starting from integrated develop at `ad9e6cb`, the fork adopts editable
checkout operation with uv and stops maintaining Python release artifacts.
README is rewritten around group use, upstream attribution, the fixed initial
change summary, demo, and setup. PACKAGING.md now covers checkout operations.
AGENTS.md and .agents/README.md make future records proportional to the change.

The Python CI distribution-build step and inherited Pixi files/settings are
removed. Pixi used obsolete demo paths, installed upstream from PyPI, and
provided a competing package upload workflow. The project documentation URL
now points to the fork README. Python build metadata, entry points, frontend
assets, and Docker's internal non-editable install remain intact.

Operator workflow: select a reviewed checkout, run
`uv sync --locked --extra web --no-dev`, then
`uv run --no-sync multivisor -c /absolute/path/to/multivisor.conf`.
Stop services before updating their editable checkout; retain the previous
commit for rollback. See PACKAGING.md for peer-host setup and full steps.

Validation passed on local Python 3.14: lock freshness, locked web-only and
web-plus-CLI sync, both console help commands, import resolving to this
checkout, HTTP root/favicon responses through Flask's test client, local
documentation links, and git diff whitespace checks. The CI edit only removes
the distribution-build step. Runtime matrices and the live demo were not
repeated because no application code, dependencies, UI, or launcher changed.
Historical migration details below are preserved.

## 2026-09-06 — Upstream RC3 integration and release-only artifacts

- Status: **local validation complete on `refactor/upstream-rc3-sync`; GitHub
  CI remains pending**
- Starting integration point: fork `develop` at `6de4648`
- Upstream reference: `upstream/develop` at `f345835` (`v7.0.0rc3`)
- Additional integrated branches: `feature/full-example-launcher` at
  `34088f4` and `fix/sse-heartbeat` at `97484ea`

### Objective and scope

Integrate the upstream Vue/Vuetify RC3 frontend work with this fork's Python
3.12–3.14 modernization, Windows demo workflow, and reverse-proxy SSE
heartbeat. Keep the fork's newer Node/Vite dependency baseline and its locked
uv environment rather than reverting to the older upstream JavaScript or Python
tooling.

This integration also establishes a release-artifact boundary: normal
`develop`, feature, fix, and refactor work must not create or publish wheels.
Direct checkout and Git-reference installs remain the development workflow.
Only a release that has reached `main` may build a wheel/sdist, inspect it, and
publish it. Generated frontend assets in `multivisor/server/dist/` remain
versioned package input; they are distinct from the ignored Python `dist/`
release-artifact directory.

### Reconciliation decisions

1. Preserve upstream RC3 Vue source changes, including the revised process,
   group, supervisor-card, tile, toolbar, and about-page UI.
2. Preserve the fork's modern `package.json` and `package-lock.json` because
   they carry the maintained Vue/Vite dependency set. Rebuild the committed
   frontend output from that lockfile after every source merge.
3. Normalize the generated HTML EOL in `vite.config.mjs`; Windows checkouts
   must not emit a CRCRLF sequence in `multivisor/server/dist/index.html`.
4. Preserve the Python runtime split, uv lockfile, RPC protocol decoupling, and
   flattened `demo/` launcher from the Python-modernization branch.
5. Replace the old SSE route generator with `iter_sse_events`: it sends an
   immediate and periodic comment heartbeat, removes listeners in `finally`,
   and sets `Cache-Control: no-cache` plus `X-Accel-Buffering: no`.
6. Limit GitHub distribution builds to push events on `main`; the job does not
   publish an artifact. Publishing remains an explicit release action.

### Files and operational effects

- `src/`, `multivisor/server/dist/`, `vite.config.mjs`, `.gitattributes`, and
  `.gitignore`: upstream UI integration, reproducible generated assets, and
  safe line-ending handling.
- `pyproject.toml`, `uv.lock`, `.python-version`, Docker, CI, and runtime
  modules: retained Python 3.12–3.14 compatibility policy documented below.
- `demo/`: retained Windows launcher and the renamed manual demo topology.
- `multivisor/server/web.py`, `multivisor/server/tests/test_sse.py`, and
  `README.md`: SSE heartbeats and proxy-facing response headers with focused
  coverage and deployment notes.
- `AGENTS.md`, `PACKAGING.md`, `.github/workflows/python.yml`, and
  `.gitignore`: release-only wheel policy. The temporary
  `.release-artifacts/` directory is ignored.

### Verification plan

Run from this integration branch without adding the local icon source assets:

```console
uv lock --check
uv run --isolated --python 3.12 --extra all --frozen ruff check .
uv run --isolated --python 3.12 --extra all --frozen pytest -q
uv run --isolated --python 3.13 --extra all --frozen ruff check .
uv run --isolated --python 3.13 --extra all --frozen pytest -q
uv run --isolated --python 3.14 --extra all --frozen ruff check .
uv run --isolated --python 3.14 --extra all --frozen pytest -q
npm ci
npm run lint
npm run build
git diff --check
```

Run the Windows Python 3.12 RPC group and the `demo/run.ps1` topology check
before merging to `develop`. On a release after it reaches `main`, additionally
run `uv build --no-sources --out-dir .release-artifacts`, inspect the wheel,
publish deliberately, and remove `.release-artifacts/`.

### Actual local verification

| Check | Result |
| --- | --- |
| `uv lock --check` | Passed; 47 packages resolved |
| Core ruff, CPython 3.12 / 3.13 / 3.14 | Passed on every lane |
| Core pytest, CPython 3.12 / 3.13 / 3.14 | Each: 5 passed, 22 expected RPC-peer skips |
| Windows CPython 3.12 RPC integration | 27 passed with a real `supervisor-win` host, web server, and event-listener adapter |
| `npm ci`, `npm run lint`, `npm run build` | Passed; generated `dist/index.html` has no CRCRLF and references the packaged favicon |
| Windows `demo/run.ps1 -WebPort 22002` | HTTP 200; 3/3 Supervisors online; 23 processes; `-Stop` removed only launcher-owned process trees |
| `git diff --check` | Passed |

`npm ci` reported one moderate advisory in the lockfile's dependency tree. It
was not automatically updated because `npm audit fix` could make unrelated
dependency changes; handle it in a dedicated dependency-maintenance branch.
No Python wheel or sdist was generated during this integration validation.

## 2026-08-21 — Python 3.14 runtime modernization

- Status: **implementation and local Windows/Linux validation complete on
  `refactor/python-upgrade`; Ubuntu GitHub lanes await CI**
- Starting commit: `afd9129` (`refactor/uv-project`)
- Target: CPython 3.14 default runtime, CPython 3.12 package floor

### Objective

Move Multivisor off the near-end-of-life Python 3.10 support lane, make current
stable CPython 3.14 the default development and container runtime, and retain a
practical compatibility window across 3.12, 3.13, and 3.14. Preserve the REST,
SSE, ZeroRPC, CLI, configuration, and frontend contracts.

This entry intentionally contains enough context and commands to reproduce the
upgrade directly from `afd9129` without relying on the conversation that led to
it.

### Baseline inventory

At `afd9129`:

| Concern | Baseline |
| --- | --- |
| Package floor | `requires-python = ">=3.10"` |
| Local default | `.python-version` = `3.12` |
| CI | Windows and Ubuntu on 3.10 and 3.12 |
| Docker | `python:3.12-alpine` build and runtime stages |
| gevent declaration | `gevent>=24.2.1` |
| Supervisor declaration | Installed transitively by `rpc`, `web`, and `all` |
| Python modernization lint | None |
| Lockfile | Universal uv lock spanning Python 3.10+ |

The repository tests passed on CPython 3.10 and 3.12 before this migration.

### Runtime policy and rationale

The chosen policy is:

- `requires-python = ">=3.12"`;
- `.python-version = 3.14`;
- central web/CLI CI lanes for 3.12, 3.13, and 3.14 on Windows and Ubuntu;
- Supervisor/RPC integration lanes on Unix 3.12, 3.13, and 3.14 and Windows
  3.12;
- Windows cross-runtime lanes with Python 3.13 and 3.14 central environments
  and a Python 3.12 `supervisor-win` RPC-host environment;
- standard GIL-enabled CPython only; free-threaded `3.14t` is unsupported;
- Docker build and runtime stages use `python:3.14-alpine`.

Why the package floor is 3.12 rather than 3.14:

1. Python 3.10 reaches end of life in October 2026, so retaining it would buy
   very little support time.
2. Python 3.12 remains in security support through October 2028 and provides a
   useful conservative lane for deployed Supervisor environments.
3. Python 3.14 is the current stable bugfix release and remains supported
   through October 2030, making it the right default and container target.
4. A 3.12 floor permits the project to use modern Python-only code while CI
   still proves that the oldest advertised interpreter works.

Primary lifecycle source: <https://devguide.python.org/versions/>.

### Dependency compatibility findings

#### gevent and greenlet

The old lower bound, `gevent>=24.2.1`, was not a valid declaration for Python
3.14 because it allowed versions released before 3.14 support. The new floor is
`gevent>=25.9.1`; the committed lock currently selects a newer compatible
release. gevent publishes CPython 3.14 wheels but explicitly does not support
free-threaded Python, which is why `3.14t` is excluded.

Primary sources:

- <https://docs.gevent.org/changelog.html>
- <https://docs.gevent.org/install.html>
- <https://pypi.org/project/gevent/>

#### Supervisor on Unix

Supervisor 4.3.0 is the supported Unix peer floor and current release line. It
is used by the private `rpc-test` dependency group and the explicit Docker extra. The Docker image
therefore remains a self-contained demo, while ordinary web and CLI installs
stay independent of a local Supervisor installation.

Primary source: <https://pypi.org/project/supervisor/>.

#### supervisor-win blocker and peer-runtime decision

`supervisor-win 4.7.0` declares `pywin32>228,<=306`. `pywin32 306` has no source
distribution and provides wheels only through CPython 3.12. A clean Windows
3.13 or 3.14 resolution therefore fails before Multivisor code runs:

```text
Distribution pywin32==306 can't be installed ...
Python 3.13 uses cp313, but pywin32 306 only provides cp310/cp311/cp312.
```

This is upstream metadata, not a uv lockfile accident. The migration handles it
without claiming that Multivisor owns or fixes Supervisor:

1. Supervisor is treated as a peer runtime for the two RPC adapters. The
   in-process `multivisor.rpc` module and the `multivisor-rpc` event listener
   execute in the same environment as an existing supervisord process.
2. The central `multivisor` web process and `multivisor-cli` do not run
   Supervisor internally. They can use Python 3.14 even when a Windows RPC host
   uses Python 3.12, and the processes may be on separate machines.
3. Public `rpc`, `web`, and `all` extras do not install Supervisor. The `rpc`
   extra supplies ZeroRPC, while the administrator owns the Supervisor peer.
4. There is no `pywin32` override. Windows Supervisor/RPC integration remains
   on Python 3.12, respecting `supervisor-win`'s released metadata. Core tests
   still cover Windows 3.13 and 3.14 without installing Supervisor.
5. The private `rpc-test` dependency group selects Unix `supervisor` on Unix
   and `supervisor-win` only on Windows below Python 3.13. CI uses that group
   only in supported RPC lanes.
6. Docker receives Unix Supervisor through a separate `docker` extra, keeping
   the demo/runtime image explicit while central-only installs remain lean.

Primary sources:

- <https://pypi.org/project/supervisor-win/>
- <https://github.com/alexsilva/supervisor/blob/windows/setup.py>
- <https://pypi.org/project/pywin32/>
- <https://docs.astral.sh/uv/concepts/resolution/>

#### Distribution selection and the same-wheel topology

No separate Multivisor build is required for the Python 3.14 central process
and Python 3.12 Windows RPC host. Multivisor is pure Python, and its wheel is a
universal `py3-none-any` distribution with `Requires-Python: >=3.12`. Both
environments install that same artifact:

| Process role | Recommended runtime | Package selection | Supervisor |
| --- | --- | --- | --- |
| Central web | Python 3.14 | `multivisor[web]` | Not installed |
| Central CLI | Python 3.14 | `multivisor[cli]` | Not installed |
| Unix RPC host | Python 3.12–3.14 | `multivisor[rpc]` | Existing Supervisor 4.3.0+ peer |
| Windows RPC host | Python 3.12 | `multivisor[rpc]` | Existing `supervisor-win 4.7.0` peer |

The installer behavior comes from distribution metadata:

- `requires-python` is written into wheel/sdist metadata, so pip and uv filter
  index releases against the active interpreter;
- wheel compatibility tags select implementation, ABI, and platform artifacts;
- environment markers choose conditional dependencies;
- extras choose role-specific dependencies from the same Multivisor release.

GitHub repository settings do not perform that selection. A PyPI install lets
the resolver choose the newest compatible published release. A direct Git
install first selects an exact commit, tag, or branch and then builds that
checkout using its `pyproject.toml`; it cannot fall back to another commit if
the selected source is incompatible. `PACKAGING.md` contains copy-pasteable
examples and the maintained release rules.

#### ZeroRPC

ZeroRPC 0.6.3 is old, so successful import is insufficient evidence. Existing
integration tests perform real calls through the Supervisor/ZeroRPC bridge;
the final validation ledger must show those tests passing in every supported
RPC lane. Any unexercised introspection path remains a documented risk rather
than an assumed success.

Primary source: <https://pypi.org/project/zerorpc/>.

### Architecture change required by the upgrade

The independent web process previously imported `Faults.FAILED` and
`RUNNING_STATES` from the installed Supervisor package. Those values are stable
wire-protocol constants, and importing an entire platform Supervisor runtime
just for them coupled the web installation to the Windows dependency blocker.

The migration adds `multivisor/supervisor_protocol.py` containing:

```python
FAULT_FAILED = 30
RUNNING_STATES = frozenset({10, 20, 30})
```

These values match Supervisor 4.x (`FAILED=30`; `STARTING=10`, `RUNNING=20`,
`BACKOFF=30`) and have a focused regression test. RPC modules still import the
real Supervisor API because they run inside the Supervisor environment.

Primary protocol sources:

- <https://github.com/Supervisor/supervisor/blob/4.3.0/supervisor/xmlrpc.py>
- <https://github.com/Supervisor/supervisor/blob/4.3.0/supervisor/states.py>

### File-by-file migration recipe

Starting from a clean checkout of `afd9129`, create the branch:

```console
git switch refactor/uv-project
git switch -c refactor/python-upgrade
```

Then apply these changes:

1. `pyproject.toml`
   - change `requires-python` from `>=3.10` to `>=3.12`;
   - add 3.12, 3.13, and 3.14 classifiers;
   - raise gevent to `>=25.9.1`;
   - remove Supervisor packages from `rpc`, `web`, and `all`;
   - add `docker = ["supervisor>=4.3.0; platform_system != 'Windows'"]`;
   - keep the default `dev` group limited to pytest, requests, and ruff;
   - add a private `rpc-test` group with Unix Supervisor and with
     `supervisor-win` only for Windows Python versions below 3.13;
   - do not add a `pywin32` override;
   - disable implicit setuptools package data, exclude the two internal test
     packages, and retain explicit `multivisor.server` package data for the
     generated frontend;
   - configure ruff for Python 3.12 with fatal syntax/import rules plus the
     `UP` modernization rules.
2. `.python-version`
   - replace `3.12` with `3.14`.
3. `.github/workflows/python.yml`
   - add a core Windows/Ubuntu 3.12/3.13/3.14 matrix that installs
     `--extra all` without Supervisor;
   - add an RPC matrix for Unix 3.12/3.13/3.14 and Windows 3.12 using
     `--group rpc-test`;
   - add Windows cross-runtime jobs that create Python 3.13 and 3.14 central
     environments and an isolated `.venv-rpc` Python 3.12 Supervisor host;
   - make RPC jobs fail when the Supervisor peer or adapter is absent rather
     than silently accepting skipped integration tests;
   - check lockfile freshness, then run ruff, tests, and distribution builds in
     the appropriate jobs.
4. `docker/Dockerfile`
   - use `python:3.14-alpine` in both stages;
   - sync the locked `docker`, `rpc`, and `web` extras;
   - normalize the copied demo executables as a defensive CRLF fallback.
5. `multivisor/supervisor_protocol.py`
   - add the stable protocol constants shown above.
6. `multivisor/multivisor.py`
   - import the local constants instead of importing Supervisor in the web
     process.
7. `multivisor/tests/test_supervisor_protocol.py`
   - assert the exact wire values.
8. `multivisor/client/{http,repl,util}.py`, `multivisor/multivisor.py`,
   `multivisor/rpc.py`, `multivisor/server/{rpc,web}.py`, and
   `multivisor/util.py`
   - run `ruff check . --fix`; the first pass identified 102 modernization
     sites and applied 98 safe fixes;
   - manually remove the remaining Python 2 compatibility imports, obsolete
     future import, unicode prefixes, old-style classes, two-argument
     `super()`, deprecated `logging.warn`, and other Python-floor dead paths;
   - replace deprecated/broad constructs only where semantics are preserved;
     do not change public messages, URLs, process states, or protocol payloads.
9. Test layout and coverage
   - make Supervisor fixtures opt-in rather than session-autouse, so core tests
     can prove that web/CLI imports do not require Supervisor;
   - allow `MULTIVISOR_TEST_SUPERVISORD`,
     `MULTIVISOR_TEST_PROCESS_PYTHON`, and
     `MULTIVISOR_TEST_RPC_COMMAND` to point central tests at a separate RPC
     environment;
   - move the shared fixtures from `tests/conftest.py` to the repository-root
     `conftest.py`, where pytest can expose them to all three test trees, and
     remove the obsolete `multivisor/server/tests/conftest.py` shim;
   - add console-entry-point smoke tests, a real event-listener RPC method and
     `PROCESS_STATE_RUNNING` stream-delivery test, event-listener Supervisor
     configuration, and the protocol-constant test;
   - use `MULTIVISOR_REQUIRE_RPC_HOST=1` in RPC CI so missing executables fail.
10. `.gitignore`, `.dockerignore`, and `.gitattributes`
    - ignore the temporary `.venv-rpc/` cross-runtime environment;
    - exclude every `.venv*` directory from Docker context;
    - require LF for every Docker helper and the executable full-example scripts.
11. `docker/bin/{CT2,Lima,demo,exits,talkative,vacuum,wago}` and
    `demo/{demo,exits,talkative}`
    - use `#!/usr/bin/env python3`; together with LF normalization this prevents
      Linux containers from trying to execute `python\r` after a Windows checkout.
12. `README.md`, `PACKAGING.md`, `AGENTS.md`, and `.agents/*`
    - synchronize setup, support policy, peer-runtime caveat, and validation.

Regenerate the universal lockfile only after metadata edits:

```console
uv lock
uv lock --check
```

Expected lockfile effects include a Python floor of 3.12, current gevent and
greenlet artifacts for CPython 3.14, and removal of Python-3.10-only backports.
The lock deliberately retains `pywin32 306` behind the Windows/Python-below-3.13
RPC-test marker. Python 3.13 and 3.14 core environments never select it.

### Validation procedure

Do not replace `.venv` if it is running the local web server. Use isolated
environments for the core web/CLI matrix:

```console
uv lock --check
uv run --isolated --python 3.12 --extra all --frozen ruff check .
uv run --isolated --python 3.12 --extra all --frozen pytest -q -rs
uv run --isolated --python 3.13 --extra all --frozen ruff check .
uv run --isolated --python 3.13 --extra all --frozen pytest -q -rs
uv run --isolated --python 3.14 --extra all --frozen ruff check .
uv run --isolated --python 3.14 --extra all --frozen pytest -q -rs
```

Skipped Supervisor tests are expected in those core environments. Run full RPC
integration separately:

```console
# Unix: repeat for 3.12, 3.13, and 3.14
uv run --isolated --python 3.14 --extra all --group rpc-test --frozen pytest -q

# Windows: supervisor-win is supported only on 3.12
$env:MULTIVISOR_REQUIRE_RPC_HOST = "1"
uv run --isolated --python 3.12 --extra all --group rpc-test --frozen pytest -q
```

The Linux matrix can also be reproduced from PowerShell with isolated Debian
containers; each container has its own network namespace, so fixed integration
ports do not collide:

```powershell
$source = (Get-Location).Path
foreach ($python in @('3.12', '3.13', '3.14')) {
    docker run --rm --mount "type=bind,source=$source,target=/workspace" `
        --workdir /workspace --env MULTIVISOR_REQUIRE_RPC_HOST=1 `
        "ghcr.io/astral-sh/uv:python$python-bookworm-slim" `
        uv run --isolated --python $python --extra all --group rpc-test --frozen pytest -q
}
```

On Windows, reproduce the supported split-runtime topology from PowerShell:

```powershell
uv python install 3.12 3.13 3.14
uv venv --python 3.12 .venv-rpc
$env:VIRTUAL_ENV = (Resolve-Path .venv-rpc).Path
uv sync --active --python 3.12 --frozen --extra rpc --no-default-groups --group rpc-test
$env:MULTIVISOR_TEST_SUPERVISORD = (Resolve-Path .venv-rpc\Scripts\supervisord.exe).Path
$env:MULTIVISOR_TEST_PROCESS_PYTHON = (Resolve-Path .venv-rpc\Scripts\python.exe).Path
$env:MULTIVISOR_TEST_RPC_COMMAND = (Resolve-Path .venv-rpc\Scripts\multivisor-rpc.exe).Path
$env:MULTIVISOR_REQUIRE_RPC_HOST = "1"
Remove-Item Env:VIRTUAL_ENV
uv run --isolated --python 3.13 --extra all --frozen pytest -q
uv run --isolated --python 3.14 --extra all --frozen pytest -q
```

Each run must exercise both RPC adapters: the in-process
`rpcinterface:multivisor` route and the `multivisor-rpc` event-listener route.
The central tests use the three environment variables above to launch the Python
3.12 Supervisor while the test runner and web-side model use the selected 3.13
or 3.14 central interpreter.

Build and validate the distribution only after the matrix is green:

```console
uv build --no-sources
```

On PowerShell, inspect the archive and install that exact wheel in a disposable
Python 3.14 environment:

```powershell
$wheel = (Get-ChildItem dist -Filter *.whl | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
uv run --no-project --python 3.14 python -c "import re,sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); n=set(z.namelist()); m=z.read(next(x for x in n if x.endswith('/METADATA'))).decode(); e=z.read(next(x for x in n if x.endswith('/entry_points.txt'))).decode(); h=z.read('multivisor/server/dist/index.html').decode(); q=chr(34); required={'multivisor/server/dist/index.html','multivisor/server/dist/favicon.ico','multivisor/supervisor_protocol.py'} | {'multivisor/server/dist/'+x.lstrip('/') for x in re.findall(r'(?:src|href)='+q+r'([^'+q+r']+)'+q,h) if x.lstrip('/').startswith(('assets/','favicon.ico'))}; assert required <= n; assert not any(x.startswith(('multivisor/tests/','multivisor/server/tests/')) for x in n); assert 'Requires-Python: >=3.12' in m; assert all(f'{x} =' in e for x in ('multivisor','multivisor-cli','multivisor-rpc')); print('wheel metadata and contents OK')" $wheel

$wheelCheck = Join-Path $env:TEMP 'multivisor-wheel-check'
if (Test-Path $wheelCheck) { throw "Refusing to reuse $wheelCheck" }
try {
    uv venv --python 3.14 $wheelCheck
    $python = Join-Path $wheelCheck 'Scripts\python.exe'
    uv pip install --python $python ("{0}[all]" -f $wheel)
    & (Join-Path $wheelCheck 'Scripts\multivisor.exe') --help
    & (Join-Path $wheelCheck 'Scripts\multivisor-cli.exe') --help
    & $python -c "import importlib.util; assert importlib.util.find_spec('supervisor') is None; print('central wheel has no Supervisor')"
} finally {
    if (Test-Path $wheelCheck) { Remove-Item -LiteralPath $wheelCheck -Recurse -Force }
}
```

Then validate the container entry points:

```console
docker build -f docker/Dockerfile -t multivisor:python-3.14 .
docker run --rm multivisor:python-3.14 python --version
docker run --rm multivisor:python-3.14 multivisor --help
docker run --rm multivisor:python-3.14 multivisor-rpc --help
```

For the runtime-script check, start disposable `lid001`, `lid002`, and
`baslid001` containers on an isolated network, expose the web service on an
unused host port, and assert HTTP 200 plus three online Supervisor entries. This
is necessary because command-help smoke tests do not execute the copied helper
scripts and therefore cannot detect a CRLF shebang regression. Remove the test
containers and network afterward. The following is the complete PowerShell
topology check used for this migration:

```powershell
$network = 'mv-python314-final-net'
$containers = @('mv-python314-final-lid001', 'mv-python314-final-lid002', 'mv-python314-final-baslid001')
if (Get-NetTCPConnection -State Listen -LocalPort 22200 -ErrorAction SilentlyContinue) { throw 'Port 22200 is in use' }
foreach ($container in $containers) {
    docker container inspect $container *> $null
    if ($LASTEXITCODE -eq 0) { throw "Refusing to reuse $container" }
}
docker network inspect $network *> $null
if ($LASTEXITCODE -eq 0) { throw "Refusing to reuse $network" }
docker network create $network | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Failed to create test network' }
try {
    docker run -d --name $containers[1] --network $network --network-alias lid002 multivisor:python-3.14 supervisord -c /etc/supervisord/lid002.conf | Out-Null
    docker run -d --name $containers[2] --network $network --network-alias baslid001 multivisor:python-3.14 supervisord -c /etc/supervisord/baslid001.conf | Out-Null
    docker run -d --name $containers[0] --network $network --network-alias lid001 -p 127.0.0.1:22200:22000 multivisor:python-3.14 supervisord -c /etc/supervisord/lid001.conf | Out-Null
    $healthy = $false
    for ($attempt = 0; $attempt -lt 80; $attempt++) {
        try {
            $page = Invoke-WebRequest http://127.0.0.1:22200/ -TimeoutSec 2
            $data = Invoke-RestMethod http://127.0.0.1:22200/api/data -TimeoutSec 2
            $supervisors = @($data.supervisors.PSObject.Properties)
            $online = @($supervisors | Where-Object { $_.Value.running }).Count
            $processes = 0
            foreach ($item in $supervisors) { $processes += @($item.Value.processes.PSObject.Properties).Count }
            if ($page.StatusCode -eq 200 -and $supervisors.Count -eq 3 -and $online -eq 3 -and $processes -ge 20) { $healthy = $true; break }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    if (-not $healthy) { throw 'Docker topology did not become healthy' }
    "HTTP=$($page.StatusCode) supervisors=$($supervisors.Count) online=$online processes=$processes"
} finally {
    foreach ($container in $containers) { docker rm -f $container 2>$null | Out-Null }
    docker network rm $network 2>$null | Out-Null
}
```

### Verification ledger

The migration deliberately records failed iterations as well as the final
results, because each failure explains a constraint or guard added by this
change.

| Iteration check | Observed result |
| --- | --- |
| Original Windows Python 3.13 all-extras resolution | Failed as expected at `pywin32==306`; established the upstream blocker |
| Windows Python 3.14 core after peer-runtime split, before event-listener test | 3 passed, 19 skipped; skips were Supervisor-dependent tests |
| Windows Python 3.12 full suite before event-listener test | 22 passed |
| Windows Python 3.14 central to Python 3.12 rpcinterface host | 21 passed, 1 skipped |
| Focused Python 3.14 central to Python 3.12 event-listener host | 1 passed |
| First Docker topology on a Windows checkout | Helper programs failed with `python\r`; led to LF attributes, Python 3 shebangs, and the Docker normalization fallback |
| Single-container Docker diagnostic | Central retries were expected because `lid002` and `baslid001` DNS peers were absent; validation was corrected to the intended three-container topology |
| First wheel after package-discovery exclusion | Still contained tests because setuptools-scm supplied tracked files as implicit package data; fixed with `include-package-data = false` and rebuilt |

Final local results on Windows 11:

| Check | Result |
| --- | --- |
| uv lock consistency | Passed: `uv lock --check`, 47 packages resolved |
| Ruff modernization rules | Passed on isolated CPython 3.12, 3.13, and 3.14; final post-edit 3.14 rerun also passed |
| Windows core CPython 3.12/3.13/3.14 | Each: 3 passed, 21 expected Supervisor-peer skips |
| Ubuntu core CPython 3.12/3.13/3.14 | CI matrix configured; awaits GitHub PR/merge CI because the local host is Windows |
| Windows CPython 3.12 RPC integration | 24 passed, including both adapters and actual process-event forwarding |
| Debian Linux CPython 3.12/3.13/3.14 RPC integration | Each: 24 passed with 5 gevent `fork()` deprecation warnings; no failures |
| Ubuntu CPython 3.12/3.13/3.14 RPC integration | CI matrix configured with missing-peer failure enforcement; awaits GitHub PR/merge CI |
| Windows 3.13 central to 3.12 RPC-host | 23 passed, 1 expected host-only entry-point skip |
| Windows 3.14 central to 3.12 RPC-host | 23 passed, 1 expected host-only entry-point skip |
| Wheel and sdist build | Passed with `uv build --no-sources`; wheel tag is `py3-none-any` and `Requires-Python` is `>=3.12` |
| Clean Python 3.14 wheel install | Passed; web and CLI help worked and Supervisor was absent from the central environment |
| Bundled web assets and wheel scope | Passed; index, favicon, and referenced assets present; 0 internal test-package entries |
| Python 3.14 Docker build/smoke | Passed on Python 3.14.7; `multivisor` and `multivisor-rpc` help passed |
| Disposable Docker runtime topology | HTTP 200; 3 of 3 Supervisors online; 27 processes; all temporary containers/network removed |

### Intended impact

- Structural: yes. The web/CLI runtime is decoupled from the local Supervisor
  distribution; Supervisor becomes a peer for RPC, an explicit Docker
  dependency, and a private `rpc-test` dependency. Core and RPC CI lanes are
  separated, with a cross-runtime Windows topology test.
- Functional: no intentional public behavior change. REST, SSE, ZeroRPC, CLI,
  and INI contracts are to remain stable. Both RPC deployment modes now have
  explicit round-trip coverage.
- Visual: none. No Vue source, CSS, or generated frontend asset is changed by
  this migration.
- Operational: Python 3.10 and 3.11 installations are no longer supported;
  default development and containers move to standard CPython 3.14. A Windows
  `supervisor-win` RPC host stays on Python 3.12, while the central process may
  independently move to 3.14 using the same Multivisor wheel.

### Follow-up: Windows demo launcher and layout (2026-09-06)

The repository's historical full-example instructions required four terminals:
three `supervisord` instances plus one central web process. On Windows that
also leaves the runtime split implicit: `supervisor-win` and its in-process
`multivisor.rpc` adapter must use Python 3.12, while the central server uses
Python 3.14. The former `examples/full_example/` directory has been flattened
to `demo/`: this is one manual integration demo rather than a family of usage
examples. `demo/run.ps1` makes its topology repeatable.

It verifies that `.venv-rpc` is Python 3.12 and recreates it with the private
`rpc-test` group only when missing or incompatible, synchronizes the central
`.venv` with the `web` extra, launches the three RPC hosts and central web
server in the background, waits for HTTP 200, and records only its own process
IDs. `-Stop` uses that state file and
`taskkill /T` to terminate exactly those process trees; it refuses to guess at
or stop an unrecorded user service. `-WebPort` defaults to 22000 and makes a
side-by-side test possible when a user already owns that port.

`supervisor-win` failed to locate the bare `python` commands in the original
Unix-oriented demo INI files. The launcher therefore writes ignored,
same-directory `*.windows.runtime.conf` copies with the Python 3.12 executable
quoted in each program command. Keeping the copies beside the originals
preserves Supervisor's `%(here)s` expansion for programs and logs. The source
INI files are unchanged, so Unix usage remains unchanged.

Changed files:

1. `demo/run.ps1`: Windows launcher, port/health checks,
   temporary runtime-config generation, and PID-scoped cleanup.
2. `.gitignore` and `demo/.gitignore`: exclude the launcher's
   transient JSON/runtime config plus normal example logs/PID files.
3. `README.md`: adds the one-command Windows workflow and `-Stop`/`-WebPort`
   usage.

Reproduce the validation without disturbing an existing server on 22000:

```powershell
.\demo\run.ps1 -WebPort 22001
$data = Invoke-RestMethod http://127.0.0.1:22001/api/data -TimeoutSec 5
$supervisors = @($data.supervisors.PSObject.Properties)
$online = @($supervisors | Where-Object { $_.Value.running }).Count
$processes = 0
foreach ($item in $supervisors) { $processes += @($item.Value.processes.PSObject.Properties).Count }
"supervisors=$($supervisors.Count) online=$online processes=$processes"
.\demo\run.ps1 -Stop
```

Actual Windows result after the `demo/` move: HTTP 200; 3 of 3 Supervisors
online; 23 demo processes in the snapshot (20 RUNNING and 3 expected STARTING
or restarting), with no FATAL process state; `-Stop` released ports 9011,
9012, 9021, 9022, 9031, 9032, and 22001 and removed its state/runtime-config
files. The 3.12 RPC-host integration suite passed 24 tests after its fixture
was redirected to `demo/{demo,exits}`. This is an operational layout change
only: no REST, SSE, ZeroRPC, CLI, Vue, or packaged frontend behavior changes.

### Rollback

Before merge, switch back to `refactor/uv-project`. After merge, reverting the
single migration commit restores the prior runtime policy. Do not restore only
`.python-version`: `pyproject.toml`, `uv.lock`, CI, Docker, dependency extras,
and the Supervisor protocol decoupling form one coherent migration and must be
rolled back together.
