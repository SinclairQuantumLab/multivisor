# Checkout operations

This fork is operated from a source checkout with an editable uv environment.
There is no wheel publication or distribution-artifact workflow, including on
`main`. The filename is retained so existing documentation links keep working.

## Environment and service startup

From the selected checkout:

```console
uv sync --locked --extra web --no-dev
uv run --no-sync multivisor --bind 127.0.0.1:22000 -c /absolute/path/to/multivisor.conf
```

`--locked` rejects an out-of-date lockfile; it does not upgrade dependencies.
`--no-sync` runs the prepared environment without modifying it at startup.
Include all roles you need when synchronizing, for example `--extra web
--extra cli`. An exact `uv sync` can remove packages outside the selected
dependency set.

Service managers should invoke the prepared executable directly:

- Windows: `C:\path\to\multivisor\.venv\Scripts\multivisor.exe`
- Unix: `/path/to/multivisor/.venv/bin/multivisor`

Use absolute paths for the executable and config, and the checkout as the
working directory. Keep operational checkouts separate from development
checkouts; an editable environment continues to read from its source directory.

## Supervisor and RPC hosts

The web server and CLI communicate with peers; they do not start Supervisor.
Each managed host needs either the in-process `multivisor.rpc` interface or
the `multivisor-rpc` event-listener bridge in its Supervisor environment.

| Role | Python | Dependencies |
| --- | --- | --- |
| Central web / CLI | 3.14 recommended; 3.12–3.14 supported | `web` / `cli` extras |
| Unix Supervisor/RPC host | 3.12–3.14 | Supervisor 4.3.0+ and `rpc` extra |
| Windows Supervisor/RPC host | 3.12 | supervisor-win 4.7.0 and `rpc` extra |

The Windows limit follows supervisor-win's pywin32 constraint. Public extras
do not install, upgrade, or override Supervisor.

For an existing Supervisor environment, install this checkout using that
environment's Python. Replace the interpreter path with the actual one:

```console
uv pip install --python /path/to/supervisor-environment/python -e ".[rpc]"
```

This additive installation preserves the host's peer runtime. It resolves the
RPC dependencies from project metadata, not `uv.lock`; retain that host's own
dependency management. Do not apply an exact project sync to an independently
managed Supervisor environment. For a disposable locked demo/RPC test host,
use the project's `rpc-test` group as described in README and AGENTS.

Choose one adapter. For the in-process interface, add to `supervisord.conf`:

```ini
[rpcinterface:multivisor]
supervisor.rpcinterface_factory = multivisor.rpc:make_rpc_interface
bind=127.0.0.1:9002
```

Alternatively, configure an event listener (use its environment's absolute
executable path):

```ini
[eventlistener:multivisor-rpc]
command=/path/to/supervisor-environment/bin/multivisor-rpc --bind 127.0.0.1:9002
events=PROCESS_STATE,SUPERVISOR_STATE_CHANGE
```

On Windows use a quoted executable path with forward slashes for Supervisor's
command parser. Restart/reconfigure the Supervisor host as appropriate for the
chosen adapter. For remote access, bind to the host's private interface and
allow only the central server to reach the RPC port.

## Authentication and reverse proxies

To enable the built-in web login, add `username` and `password` under
`[global]` and set `MULTIVISOR_SECRET_KEY` in the service environment.
Generate a secret with:

```console
uv run --no-sync python -c "import secrets; print(secrets.token_hex(32))"
```

Keep the secret stable across restarts and protect the config containing the
credentials. Use HTTPS at the reverse proxy for remote web access.

The live-update endpoint `/api/stream` sends an immediate SSE comment and a
heartbeat after 15 seconds without an event. It sends `Cache-Control:
no-cache` and `X-Accel-Buffering: no`. Configure the proxy for streaming and an
idle timeout longer than the heartbeat interval; these headers cannot override
every proxy policy.

## Updates and rollback

1. Record `git rev-parse HEAD` and stop the service.
2. Fetch updates and select a reviewed commit or tag. On an operational branch
   that tracks its remote, `git pull --ff-only` accepts only a fast-forward.
3. Run `uv sync --locked --extra web --no-dev` (with any other required extras).
4. Restart and verify the web route and connections to the managed hosts.

For rollback, stop the service, check out the previously recorded commit in a
clean operational checkout, synchronize its lockfile with the same extras,
then restart. Keep configuration backups separately. Never switch branches or
rewrite source under a running operational process.

## Build machinery retained for installation

`pyproject.toml`, setuptools, and the console-script declarations support
editable installation. Installer caches may contain intermediate wheels;
maintainers do not distribute or curate them.

The web server reads `multivisor/server/dist/`. This committed frontend output
is runtime input, so it is retained even without Python distribution releases.
Frontend contributors rebuild it with `npm ci`, `npm run lint`, and
`npm run build`.

The optional Docker image uses a non-editable install because its final stage
copies the virtual environment without the source checkout. This remains an
internal image-build step and needs no separately managed wheel.

uv and npm are the maintained environment tools; the inherited Pixi setup has
been removed. See [AGENTS.md](AGENTS.md) for contributor checks and
[the historical engineering record](.agents/CHANGELOG.md) for the initial
migration rationale.
