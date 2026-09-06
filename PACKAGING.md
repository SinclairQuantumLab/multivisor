# Git dependency operations

This fork is consumed as a Python package from an immutable Git tag. The
operational repository owns configuration, service definitions, and its
`uv.lock`; this repository owns application source, tests, and release tags.
Direct Git installation builds from the selected repository revision, so no
wheel publication is necessary for normal group operation.

## Environment and service startup

From an operational project such as `multivisor-web`:

```console
uv add "multivisor[web] @ git+https://github.com/SinclairQuantumLab/multivisor.git@<release-tag>"
uv sync --frozen
uv run multivisor --bind 127.0.0.1:22000 -c /absolute/path/to/multivisor.conf
```

Replace `<release-tag>` with an approved, immutable fork tag. `uv add` writes
the direct Git requirement and resolves it to a commit in `uv.lock`; `uv sync
--frozen` then recreates exactly that environment. Include all roles in the
same requirement when needed, for example `multivisor[web,cli]`. Do not use a
floating branch for a production service. A branch such as `develop` is useful
only for a disposable integration test and does not automatically fall back to
an older release on an incompatible Python version.

Service managers should invoke the prepared executable directly:

- Windows: `C:\path\to\multivisor-web\.venv\Scripts\multivisor.exe`
- Unix: `/path/to/multivisor-web/.venv/bin/multivisor`

Use absolute paths for the executable and config, and the operational project
as the working directory. Keep its credentials and configuration out of Git.

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
uv pip install --python /path/to/supervisor-environment/python "multivisor[rpc] @ git+https://github.com/SinclairQuantumLab/multivisor.git@<release-tag>"
```

This additive installation preserves the host's peer runtime. It resolves the
RPC dependencies from the tagged package metadata, not the central project's
`uv.lock`; retain that host's own dependency management. Do not apply an exact
project sync to an independently managed Supervisor environment. For a
disposable locked demo/RPC test host, use this repository's `rpc-test` group as
described in README and AGENTS.

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

1. Record `uv tree` and stop the service.
2. Change the direct Git requirement to a reviewed release tag with `uv add`.
3. Run `uv lock` and commit the resulting `pyproject.toml` and `uv.lock` in the
   operational repository.
4. Run `uv sync --frozen`, restart, and verify the web route and connections to
   the managed hosts.

For rollback, stop the service, restore the previous operational
`pyproject.toml` and `uv.lock`, synchronize with `uv sync --frozen`, then
restart. Keep configuration backups separately.

## Package and release mechanics

`pyproject.toml`, setuptools, and the console-script declarations define a
normal Python package. A direct Git dependency invokes that build machinery at
install time. On an approved release, build and inspect with:

```console
uv build --no-sources
```

Do not commit `dist/` or any generated wheel/sdist. Publishing to a package
index is optional and must be an explicit release decision; it is not required
by the Git dependency workflow.

The web server reads `multivisor/server/dist/`. This committed frontend output
is runtime input, so it is retained even without Python distribution releases.
Frontend contributors rebuild it with `npm ci`, `npm run lint`, and
`npm run build`.

The optional Docker image uses a non-editable install because its final stage
copies the virtual environment without the source checkout. This remains an
internal image-build step.

uv and npm are the maintained environment tools; the inherited Pixi setup has
been removed. See [AGENTS.md](AGENTS.md) for contributor checks and
[the historical engineering record](.agents/CHANGELOG.md) for the initial
migration rationale.
