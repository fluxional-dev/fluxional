from typer.testing import CliRunner
from fluxional.cli import run_command_line, app
import os
import pytest

runner = CliRunner()


def test_run_command_line():
    with pytest.raises(SystemExit):
        run_command_line()


def test_deploy():
    result = runner.invoke(
        app,
        [
            "deploy",
            "mock_file.handler",
            "--path",
            os.path.join(os.getcwd(), "tests/cli"),
        ],
    )

    assert "cli_test" in result.stdout
    assert "cli_deploy" in result.stdout


def test_destroy():
    result = runner.invoke(
        app,
        [
            "destroy",
            "mock_file.handler",
            "--path",
            os.path.join(os.getcwd(), "tests/cli"),
        ],
    )

    assert "cli_test" in result.stdout
    assert "cli_destroy" in result.stdout


def test_sync():
    result = runner.invoke(
        app,
        [
            "sync",
            "mock_file.handler",
            "--path",
            os.path.join(os.getcwd(), "tests/cli"),
        ],
    )

    assert "cli_test" in result.stdout
    assert "cli_sync" in result.stdout


def test_dev():
    result = runner.invoke(
        app,
        [
            "dev",
            "mock_file.handler",
            "--path",
            os.path.join(os.getcwd(), "tests/cli"),
        ],
    )

    assert "cli_test" in result.stdout
    assert "cli_dev" in result.stdout
