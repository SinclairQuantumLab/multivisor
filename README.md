# Multivisor — Sinclair Quantum Lab

Forked from [tiagocoutinho/multivisor](https://github.com/tiagocoutinho/multivisor).
See the [original README](https://github.com/tiagocoutinho/multivisor/blob/develop/README.md)
for upstream documentation. This README describes our group's version.

Multivisor provides a web dashboard and optional CLI for monitoring and
controlling processes across Supervisor hosts. We maintain this fork so the
group can adapt it to its infrastructure, test changes locally, and operate
reviewed Git revisions with reproducible dependencies.

## Our starting point

The initial fork integration (2026-09-06, commit `ad9e6cb`) combines upstream
`v7.0.0rc3` (`f345835`) with these group-specific changes:

- **Reliable idle live updates:** an immediate SSE comment and a 15-second
  heartbeat, proxy buffering headers, and listener cleanup on disconnect.
- **Reproducible environments:** uv and a committed Python lockfile, a repaired
  npm toolchain/lockfile, and a committed frontend build.
- **Modern Python with independent hosts:** Python 3.14 for the central server;
  compatibility coverage for 3.12–3.14. The central server no longer requires
  a local Supervisor installation. Windows Supervisor/RPC hosts stay on 3.12.
- **A repeatable demo:** the `demo/` layout and a Windows launcher that starts
  three Supervisor hosts plus the web server and stops its own process trees.
- **Maintenance checks:** Python lint, core/RPC tests, cross-runtime CI, and
  repository guidance for both humans and coding agents.

Vue 3, Vuetify 3, and the RC3 interface improvements come from upstream.
Our frontend work integrates that baseline and maintains its build tooling.

This is the foundation for our custom repository's ongoing development, not a
rolling release changelog. Routine changes live in Git history; substantial
migration notes belong in the [engineering record](.agents/CHANGELOG.md).

## Install in an operational project

Install Git and [uv](https://docs.astral.sh/uv/getting-started/installation/).
Keep the application package separate from the group configuration and service
repository. The package is installed from a reviewed, immutable Git tag; the
consumer's `uv.lock` records the resulting commit.

```console
git clone https://github.com/SinclairQuantumLab/multivisor-web.git
cd multivisor-web
uv add "multivisor[web] @ git+https://github.com/SinclairQuantumLab/multivisor.git@<release-tag>"
uv sync --frozen
```

Replace `<release-tag>` with the approved fork tag, never a floating branch in
production. `uv add` builds the package from that Git revision; a separately
published wheel is not required. Node.js is only needed when changing the
frontend in this repository.

Create your own config outside the checkout, for example:

```ini
[global]
name=Sinclair Quantum Lab

[supervisor:lab-host]
url=lab-host:9002
```

The URL points to a Multivisor RPC adapter on that host, not Supervisor's
normal HTTP/XML-RPC port. Configure the host using the
[RPC setup instructions](PACKAGING.md#supervisor-and-rpc-hosts), then run:

```console
uv run multivisor --bind 127.0.0.1:22000 -c /absolute/path/to/multivisor.conf
```

Replace the config path with your actual path (quote paths containing spaces).
Open [localhost:22000](http://localhost:22000). For service managers, use the
environment's absolute executable path; see [operations](PACKAGING.md).

To include the optional CLI alongside the web server:

```console
uv add "multivisor[web,cli] @ git+https://github.com/SinclairQuantumLab/multivisor.git@<release-tag>"
uv sync --frozen
uv run multivisor-cli --url localhost:22000
```

## Try the demo

The demo creates sample processes for manual testing. Its Supervisor endpoints
are unauthenticated; run it on a trusted development machine.

### Windows

From the checkout:

```powershell
.\demo\run.ps1
# Open http://localhost:22000
.\demo\run.ps1 -Stop
```

The launcher prepares a Python 3.14 central environment and a separate
Python 3.12 `.venv-rpc` environment for `supervisor-win`. It returns to the
prompt after the web server responds. Use `-WebPort 22001` if 22000 is busy.
Supervisor ports 9011/9012, 9021/9022, and 9031/9032 must also be free.

### Unix

```sh
uv sync --locked --extra all --group rpc-test
mkdir -p demo/log
uv run --no-sync supervisord -c demo/supervisord_lid001.conf
uv run --no-sync supervisord -c demo/supervisord_lid002.conf
uv run --no-sync supervisord -c demo/supervisord_baslid001.conf
uv run --no-sync multivisor -c demo/multivisor.conf
```

Stop the foreground web server with Ctrl+C, then stop the demo hosts:

```sh
uv run --no-sync supervisorctl -c demo/supervisord_lid001.conf shutdown
uv run --no-sync supervisorctl -c demo/supervisord_lid002.conf shutdown
uv run --no-sync supervisorctl -c demo/supervisord_baslid001.conf shutdown
```

The existing Docker demo is also available with `docker compose up --build`;
stop it with `docker compose down`. See [docker-compose.yml](docker-compose.yml)
for its published ports.

## Operate and update

Use a dedicated operational project such as `multivisor-web`. Stop its service
before changing its locked package revision, record the installed commit with
`uv tree`, then update the Git tag with `uv add`, regenerate the lock, sync,
and restart. Python and built frontend changes take effect after process
restart.

See [Git dependency operations](PACKAGING.md) for service commands, RPC
installation, authentication, reverse proxies, and rollback. Keep local
credentials and configuration outside Git.

## Develop

```console
uv sync --locked --extra all
uv run --no-sync ruff check .
uv run --no-sync pytest -q
```

Core tests work without Supervisor; RPC tests need the host setup described in
[AGENTS.md](AGENTS.md). Standard GIL-enabled CPython 3.12, 3.13, and 3.14 are
supported; free-threaded Python is not supported.

For frontend changes, use Node.js 20.19+ and npm 10+:

```console
npm ci
npm run lint
npm run build
```

Commit the source, any lockfile changes, and regenerated
`multivisor/server/dist/` together. With the backend on port 22000,
`npm run dev` provides the Vite development UI.

We use Git Flow names: work branches merge into `develop`, and reviewed
operational releases reach `main` and receive an immutable Git tag. The tag is
the package reference used by operational projects. A release may build a wheel
for validation or later publication, but development branches never carry
distribution artifacts.

## Attribution

Multivisor was created by Tiago Coutinho and developed with upstream
contributors, including Samuel Debionne. This fork retains the
[GPL-3.0-or-later license](LICENSE).
