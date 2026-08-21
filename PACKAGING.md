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

Python development uses the committed `uv.lock`. Create or update the local
environment with all Multivisor components and the default development group:

```console
uv sync --frozen --all-extras
uv run pytest
```

When dependencies change, run `uv lock` and commit `pyproject.toml` and
`uv.lock` together. CI and release jobs should use `--frozen` or `--locked` so
they fail rather than silently changing the resolved environment.

Build the source distribution and wheel after the frontend has been rebuilt:

```console
uv lock --check
uv build --no-sources
```

Inspect or install the wheel in a clean environment before publishing it. The
wheel must contain `multivisor/server/dist/index.html`, `favicon.ico`, and all
referenced assets.

To publish a verified release:

```console
uv publish
```
