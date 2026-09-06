# Packaging

## Frontend

Use Node.js 20.19 or newer and npm 10 or newer. The lockfile contains optional
packages for every supported platform, so always use the clean-install command:

```console
npm ci
npm audit
npm run lint
npm run build
```

The production frontend is written to `multivisor/server/dist`. These generated
files are versioned deliberately: Python wheels and direct Git installs cannot
assume that Node.js is available while the Python package is being built.

After changing frontend source or dependencies, rebuild the frontend and commit
the updated source, lockfile, and `multivisor/server/dist` together.

## Python distributions

### One distribution, several runtime roles

Multivisor is pure Python and publishes one universal wheel with a Python 3.12
floor; the tested CPython lanes are 3.12, 3.13, and 3.14. Do not create a separate
"Python 3.12 RPC build" and "Python 3.14 web build": the same wheel is
installed into both environments.

| Environment | Python | Install | Supervisor relationship |
| --- | --- | --- | --- |
| Central web server | 3.14 recommended; 3.12–3.14 tested | `multivisor[web]` | None; calls remote RPC bridges |
| Central CLI | 3.14 recommended; 3.12–3.14 tested | `multivisor[cli]` | None; calls the web REST API |
| Unix RPC host | 3.12, 3.13, or 3.14 | `multivisor[rpc]` | Existing Supervisor 4.3.0+ peer in the same environment |
| Windows RPC host | 3.12 | `multivisor[rpc]` | Existing `supervisor-win 4.7.0` peer in the same environment |

The Windows RPC-host ceiling belongs to `supervisor-win 4.7.0`, which requires
`pywin32<=306`; it is not a Multivisor wheel restriction. The public `rpc`
extra therefore installs ZeroRPC but does not install or override Supervisor.

All three console-script declarations are present in the wheel. An extra
installs the dependencies needed by a role; it does not add or remove entry
point metadata. In particular, `multivisor-rpc` and the in-process
`multivisor.rpc` module still require the Supervisor peer runtime in which they
operate.

### How installers choose a compatible distribution

Python compatibility is package metadata in `pyproject.toml`, not a GitHub
repository setting:

- `[project].requires-python = ">=3.12"` becomes `Requires-Python` in wheel and
  source-distribution metadata. pip and uv reject a release when the active
  interpreter does not satisfy it and, when resolving from an index, select
  the newest compatible release.
- Wheel compatibility tags select platform, implementation, and ABI-specific
  artifacts. This project has no compiled extension, so its wheel is tagged
  `py3-none-any`; `Requires-Python` supplies the 3.12 floor.
- Environment markers on dependencies select platform/runtime-specific
  requirements. The private `rpc-test` group, for example, selects Unix
  `supervisor` on Unix and selects `supervisor-win` only on Windows below
  Python 3.13.
- Extras such as `web`, `cli`, and `rpc` select feature dependencies from the
  same distribution. They do not select different Multivisor source trees.

Installing from PyPI lets the resolver choose among published releases:

```console
uv tool install --python 3.14 "multivisor[web]"
uv pip install "multivisor[rpc]"
```

A direct Git reference selects the named commit, tag, or branch first and then
builds that checkout using its `pyproject.toml` metadata:

```console
uv pip install "multivisor[web] @ git+https://github.com/SinclairQuantumLab/multivisor.git@develop"
```

There is no fallback to another Git commit when that checkout is incompatible
with the active Python. GitHub Actions or release settings can automate builds
and uploads, but installer selection is controlled by the distribution
metadata and package index.

### Locked development and release builds

Python development uses the committed `uv.lock`. Create or update the central
web/CLI environment with the named `all` extra and default development group:

```console
uv sync --frozen --extra all
uv run pytest
```

Add the private RPC integration group only where a supported Supervisor test
runtime is required:

```console
# Unix on Python 3.12, 3.13, or 3.14; Windows on Python 3.12 only
uv sync --frozen --extra all --group rpc-test
uv run pytest
```

CI keeps these concerns separate: core web/CLI tests run on Windows and Ubuntu
for Python 3.12, 3.13, and 3.14; RPC integration runs on Unix for all three and
on Windows for 3.12. Separate Windows tests connect Python 3.13 and 3.14 central
environments to a Python 3.12 RPC-host environment.

When dependencies change, run `uv lock` and commit `pyproject.toml` and
`uv.lock` together. CI should run `uv lock --check` (or use `--locked`) to reject
a stale lockfile; `--frozen` prevents writes but deliberately skips that
freshness check.

Build the source distribution and wheel after the frontend has been rebuilt:

```console
uv lock --check
uv build --no-sources
```

Inspect or install the wheel in a clean environment before publishing it. The
wheel must contain `multivisor/server/dist/index.html`, `favicon.ico`, and all
referenced assets. It must not contain the repository's test packages;
`include-package-data = false` and the explicit `multivisor.server` package-data
list keep the wheel limited to runtime Python modules and generated web assets.

To publish a verified release:

```console
uv publish
```
