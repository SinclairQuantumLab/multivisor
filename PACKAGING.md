# Packaging

## Frontend

Use Node.js 18 or newer and npm 8 or newer. The lockfile contains optional
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

Build the source distribution and wheel after the frontend has been rebuilt:

```console
uv build
```

Inspect or install the wheel in a clean environment before publishing it. The
wheel must contain `multivisor/server/dist/index.html`, `favicon.ico`, and all
referenced assets.

To publish a verified release:

```console
uv publish
```
