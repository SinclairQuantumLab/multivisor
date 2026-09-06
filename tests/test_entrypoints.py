from importlib.util import find_spec
import shutil
import subprocess

import pytest


def assert_console_script_help(name):
    script = shutil.which(name)
    assert script is not None
    result = subprocess.run(
        [script, "--help"], capture_output=True, check=False, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout


@pytest.mark.parametrize("name", ["multivisor", "multivisor-cli"])
def test_central_console_script_help_does_not_require_supervisor(name):
    assert_console_script_help(name)


def test_rpc_console_script_help_when_supervisor_is_available():
    if find_spec("supervisor") is None:
        pytest.skip("Supervisor peer runtime is not installed")

    assert_console_script_help("multivisor-rpc")
