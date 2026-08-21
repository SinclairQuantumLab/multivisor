# Multivisor

<img width="60%" align="right" alt="multivisor web on chrome desktop app"
 title="multivisor web on chrome desktop app"
 src="doc/multivisor_desktop.png"
/>


[![Multivisor][pypi-version]](https://pypi.python.org/pypi/multivisor)
[![Python Versions][pypi-python-versions]](https://pypi.python.org/pypi/multivisor)
[![Pypi status][pypi-status]](https://pypi.python.org/pypi/multivisor)
![License][license]
[![Python][python-build]](https://github.com/SinclairQuantumLab/multivisor/actions/workflows/python.yml)

A centralized supervisor UI (Web & CLI)

* Processes status always up to date
* Reactivity through asynchronous actions
* Notifications when state changes
* Mobile aware, SPA web page
* Powerful filters
* Interactive CLI
* works on [supervisor](https://pypi.org/project/supervisor/)
  and [supervisor-win](https://pypi.org/project/supervisor-win/)

Multivisor is comprised of 3 components:

1. **web server**: gathers information from all supervisors and provides a
   dashboard like UI to the entire system
1. **multivisor RPC**: an RPC extension to supervisor used to communicate
   between each supervisord and multivisor web server
1. **CLI**: an optional CLI which communicates with multivisor web server

The web server and CLI are central components; they do not run Supervisor
internally. Each managed host runs Supervisor plus either the in-process
`multivisor.rpc` interface or the `multivisor-rpc` event-listener bridge. The
central process reaches those bridges over ZeroRPC, so the two sides may use
different Python environments or different computers.

Multivisor's tested compatibility lanes are CPython 3.12, 3.13, and 3.14.
CPython 3.14 is the recommended runtime for the central web server and CLI. On
Windows, keep a
`supervisor-win` RPC host on CPython 3.12 because its `pywin32<=306` dependency
does not provide CPython 3.13 or 3.14 wheels. This does not hold the central
component back: the same Multivisor distribution installs in both the Python
3.14 central environment and the Python 3.12 RPC-host environment.

## Installation and configuration

The configuration format is the same on Linux and Windows. The Python runtime
topology differs on Windows as described below.

Thanks to the [ESRF](https://esrf.eu) sponsorship, multivisor is able to work
well with [supervisor-win](https://pypi.org/project/supervisor-win/).

### RPC

The multivisor RPC must be installed in the same environment(s) as your
supervisord instances. The `rpc` extra installs ZeroRPC; it deliberately does
not install or replace Supervisor itself.

On Unix, use Supervisor 4.3.0 or newer with Python 3.12, 3.13, or 3.14. On
Windows, use `supervisor-win 4.7.0` on CPython 3.12 while its current dependency
constraint remains in place. These are peer-runtime requirements and therefore
are documented rather than installed by the public `rpc` extra.

From within the same python environment as your supervisord process, type:

```bash
uv pip install 'multivisor[rpc]'
```

There are two options to configure multivisor RPC: 1) as an extra
[rpcinterface](http://supervisord.org/configuration.html#rpcinterface-x-section-settings)
to supervisord or 2) an [eventlistener](http://supervisord.org/configuration.html#eventlistener-x-section-settings) process managed by supervisord.

The first option has the advantage of not requiring an extra process but it's
implementation relies on internal supervisord details. Therefore, the multivisor
author recommends using the 2nd approach.

#### Option 1: rpcinterface

Configure the multivisor rpc interface by adding the following lines
to your *supervisord.conf*:

```ini
[rpcinterface:multivisor]
supervisor.rpcinterface_factory = multivisor.rpc:make_rpc_interface
bind=*:9002
```

If no *bind* is given, it defaults to `*:9002`.

Repeat the above procedure for every supervisor you have running.

#### Option 2: eventlistener

Configure the multivisor rpc interface by adding the following lines
to your *supervisord.conf*:

```ini
[eventlistener:multivisor-rpc]
command=multivisor-rpc --bind 0:9002
events=PROCESS_STATE,SUPERVISOR_STATE_CHANGE
```

If no *bind* is given, it defaults to `*:9002`.

You are free to choose the event listener name. As a convention we propose
`multivisor-rpc`.

NB: Make sure that `multivisor-rpc` command is accessible or provide full PATH.

Repeat the above procedure for every supervisor you have running.


### Web server

The multivisor web server requires Python 3.12 or newer and is independent of
the Python used by each Supervisor host. It must be installed on a machine with
network access to the different supervisors. CPython 3.14 is recommended:

```bash
uv tool install --python 3.14 'multivisor[web]'
```

The web server is configured with a INI like configuration file
(much like supervisor itself) that is passed as command line argument.
It is usually named *multivisor.conf* but can be any filename you which.

The file consists of a `global` section where you can give an optional name to
your multivisor instance (default is *multivisor*. This name will appear on the
top left corner of multivisor the web page).

To add a new supervisor to the list simply add a section `[supervisor:<name>]`.
It accepts an optional `url` in the format `[<host>][:<port>]`. The default
is `<name>:9002`.

Here is an example:

```ini
[global]
name=ACME

[supervisor:roadrunner]
# since no url is given it will be roadrunner:9002

[supervisor:coyote]
# no host is given: defaults to coyote
url=:9011

[supervisor:bugsbunny]
# no port is given: defaults to 9002
url=bugsbunny.acme.org

[supervisor:daffyduck]
url=daffyduck.acme.org:9007
```

<img width="40%" align="right" alt="multivisor web on mobile"
 title="multivisor web on mobile"
 src="doc/multivisor_mobile.png"
/>

Once installed and configured, the web server can be started from the command
line with:

```bash
multivisor -c ./multivisor.conf
```

Start a browser pointing to [localhost:22000](http://localhost:22000).
On a mobile device it should look something like the figure on the right.

Of course the multivisor web server itself can be configured in supervisor as a
normal program.

#### Authentication

To protect multivisor from unwanted access, you can enable authentication.

Specify `username` and `password` parameters in `global` section of your configuration file e.g.:

```ini
[global]
username=test
password=test
```

You can also specify `password` as SHA-1 hash in hex, with `{SHA}` prefix: e.g.
`{SHA}a94a8fe5ccb19ba61c4c0873d391e987982fbbd3` (example hash is `test` in SHA-1).

In order to use authentication, you also need to set `MULTIVISOR_SECRET_KEY` environmental variable,
as flask sessions module needs some secret value to create secure session.
You can generate some random hash easily using python:
`python -c 'import os; import binascii; print(binascii.hexlify(os.urandom(32)))'`

### CLI

The multivisor CLI is an optional component which can be installed with:

```bash
uv tool install --python 3.14 'multivisor[cli]'
```

The CLI connects directly to the web server using an HTTP REST API.
It doesn't require any configuration.

It can be started with:

```bash
multivisor-cli --url localhost:22000
```

![CLI in action](doc/cli.svg)

# Running the docker demo

```bash
$ docker-compose build --parallel
$ docker-compose up
```

That's it!

Start a browser pointing to [localhost:22000](http://localhost:22000).

# Running the example from scratch

```bash
# Fetch the project:
git clone https://github.com/SinclairQuantumLab/multivisor
cd multivisor


# Install frontend dependencies
npm ci
# Build for production with minification
npm run build

# Create .venv from the committed lockfile. The RPC test group installs
# Supervisor for this Unix demonstration.
uv sync --frozen --extra all --group rpc-test

# Launch a few supervisors
mkdir examples/full_example/log
uv run supervisord -c examples/full_example/supervisord_lid001.conf
uv run supervisord -c examples/full_example/supervisord_lid002.conf
uv run supervisord -c examples/full_example/supervisord_baslid001.conf

# Finally, launch multivisor:
uv run multivisor -c examples/full_example/multivisor.conf
```

That's it!

Start a browser pointing to [localhost:22000](http://localhost:22000). On a mobile
device it should look something like this:

![multivisor on mobile](doc/multivisor_mobile.png)

# Technologies

![multivisor diagram](doc/diagram.png)

The `multivisor` backend runs a [flask](http://flask.pocoo.org/) web server.

The `multivisor-cli` runs a
[prompt-toolkit](http://python-prompt-toolkit.rtfd.io) based console.

The frontend is based on [vue](https://vuejs.org/) +
[pinia](https://pinia.vuejs.org/) + [vuetify](https://vuetifyjs.com/).

# Development

## Build & Install

```bash
# Install the locked central web/CLI development environment
uv sync --frozen --extra all

# Unix: add Supervisor only for RPC integration work.
uv sync --frozen --extra all --group rpc-test

# Install the locked frontend dependencies
npm ci

# build for production with minification
npm run build

# Run the test suite
uv run pytest

```

On Windows, keep the default central environment on Python 3.14 and create the
RPC test host separately on Python 3.12:

```powershell
uv venv --python 3.12 .venv-rpc
$env:VIRTUAL_ENV = (Resolve-Path .venv-rpc).Path
uv sync --active --python 3.12 --frozen --extra rpc --no-default-groups --group rpc-test
Remove-Item Env:VIRTUAL_ENV
```

See the [migration ledger](.agents/CHANGELOG.md#validation-procedure) for the
complete cross-runtime test command.

## Run

```bash
# serve at localhost:22000
uv run multivisor -c multivisor.conf
```

Start a browser pointing to [localhost:22000](http://localhost:22000)

## Development mode

You can run the backend using the vite dev server to facilitate your
development cycle:

First, start multivisor (which listens on 22000 by default):

```bash
uv run python -m multivisor.server.web -c multivisor.conf
```

Now, in another console, run the vite dev server (it will
transfer the requests between the browser and multivisor):

``` bash
npm run dev
```

That's it. If you modify `App.vue` for example, you should see the changes
directly on your browser.


[pypi-python-versions]: https://img.shields.io/pypi/pyversions/multivisor.svg
[pypi-version]: https://img.shields.io/pypi/v/multivisor.svg
[pypi-status]: https://img.shields.io/pypi/status/multivisor.svg
[license]: https://img.shields.io/pypi/l/multivisor.svg
[python-build]: https://github.com/SinclairQuantumLab/multivisor/actions/workflows/python.yml/badge.svg
