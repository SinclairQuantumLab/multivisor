"""Shared unit and integration fixtures for the repository test suite."""

from gevent.monkey import patch_all

patch_all(thread=False)


import os
import shutil
import signal
import subprocess
import sys
from time import sleep

import pytest
import requests
from requests import ConnectionError

from multivisor.multivisor import Multivisor
from multivisor.multivisor import Supervisor
from multivisor.server.web import get_parser


def rpc_host_unavailable(message):
    if os.environ.get("MULTIVISOR_REQUIRE_RPC_HOST") == "1":
        pytest.fail(message, pytrace=False)
    pytest.skip(message)


def start_process(command, env=None):
    options = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.STDOUT,
        "env": env,
    }
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True
    return subprocess.Popen(command, **options)


def stop_process(process):
    if process.poll() is not None:
        return

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        os.killpg(process.pid, signal.SIGTERM)

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def basic_options():
    args = ["-c", "tests/multivisor_test.conf"]
    parser = get_parser(args)
    options = parser.parse_args(args)
    return options


@pytest.fixture
def multivisor_instance(basic_options):
    multivisor = Multivisor(basic_options)
    return multivisor


@pytest.fixture(scope="session")
def supervisor_test001():
    supervisord = os.environ.get("MULTIVISOR_TEST_SUPERVISORD", "supervisord")
    supervisord = shutil.which(supervisord)
    if supervisord is None:
        rpc_host_unavailable(
            "Supervisor is a peer runtime; install the rpc-test dependency group "
            "to run integration tests"
        )

    environment = os.environ.copy()
    environment["MULTIVISOR_TEST_PYTHON"] = os.environ.get(
        "MULTIVISOR_TEST_PROCESS_PYTHON", sys.executable
    )
    process = start_process(
        [supervisord, "-n", "-c", "tests/supervisord_test001.conf"],
        env=environment,
    )

    address = "tcp://localhost:9073"
    supervisor = Supervisor("test1", address)
    for _ in range(50):
        if process.poll() is not None:
            raise RuntimeError("test supervisord exited before becoming ready")
        info = supervisor.read_info()
        if info["running"]:
            break
        sleep(0.1)
    else:
        raise RuntimeError("test supervisord did not become ready")

    yield process
    try:
        stop_process(process)
    except OSError:
        pass  # process already dead


@pytest.fixture(scope="session")
def supervisor_eventlistener():
    supervisord = os.environ.get("MULTIVISOR_TEST_SUPERVISORD", "supervisord")
    supervisord = shutil.which(supervisord)
    if supervisord is None:
        rpc_host_unavailable(
            "Supervisor is a peer runtime; install the rpc-test dependency group "
            "to run integration tests"
        )

    executable_suffix = ".exe" if os.name == "nt" else ""
    sibling_rpc = os.path.join(
        os.path.dirname(supervisord), f"multivisor-rpc{executable_suffix}"
    )
    rpc_command = os.environ.get("MULTIVISOR_TEST_RPC_COMMAND", sibling_rpc)
    rpc_command = shutil.which(rpc_command)
    if rpc_command is None:
        rpc_host_unavailable(
            "multivisor-rpc is not installed in the Supervisor environment"
        )
    if os.name == "nt":
        # Supervisor parses command strings with POSIX-style backslash escaping.
        rpc_command = rpc_command.replace("\\", "/")

    environment = os.environ.copy()
    environment["MULTIVISOR_TEST_RPC_COMMAND"] = rpc_command
    environment["MULTIVISOR_TEST_PYTHON"] = os.environ.get(
        "MULTIVISOR_TEST_PROCESS_PYTHON", sys.executable
    )
    process = start_process(
        [supervisord, "-n", "-c", "tests/supervisord_eventlistener.conf"],
        env=environment,
    )

    try:
        supervisor = Supervisor("eventlistener", "tcp://localhost:9076")
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError(
                    "eventlistener test supervisord exited before becoming ready"
                )
            info = supervisor.read_info()
            if info["running"]:
                break
            sleep(0.1)
        else:
            raise RuntimeError("eventlistener RPC adapter did not become ready")

        yield supervisor
    finally:
        try:
            stop_process(process)
        except OSError:
            pass  # process already dead


@pytest.fixture(scope="session")
def server(supervisor_test001, base_url):
    process = start_process(
        [
            sys.executable,
            "-m",
            "multivisor.server.web",
            "-c",
            "tests/multivisor_test.conf",
            "--bind",
            "127.0.0.1:22001",
        ]
    )
    for _ in range(20):
        if process.poll() is not None:
            raise RuntimeError("test web server exited before becoming ready")
        try:
            requests.get(base_url, timeout=1)
            break
        except ConnectionError:
            sleep(0.25)
    else:
        raise RuntimeError("test web server did not become ready")

    yield process
    try:
        stop_process(process)
    except OSError:
        pass  # process already dead


@pytest.fixture(scope="session")
def base_url():
    return "http://localhost:22001"


@pytest.fixture(scope="session")
def api_base_url(server, base_url):
    return f"{base_url}/api"
