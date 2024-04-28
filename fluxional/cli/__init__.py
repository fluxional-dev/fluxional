import typer
import os
import sys
from typing import Callable

from dotenv import load_dotenv

load_dotenv()


app = typer.Typer()
cwd = os.getcwd()


def import_method_from_handler(*, handler: str, path: str) -> Callable:
    """
    Import a method from a handler
    """
    sys.path.append(path)
    file, method = handler.split(".")
    test = __import__(file)
    return getattr(test, method)


@app.command()
def deploy(
    handler: str,
    path: str = cwd,
    show_logs: bool = True,
):
    func = import_method_from_handler(handler=handler, path=path)
    func(
        {
            "fluxional_event": "cli_deploy",
            "show_logs": show_logs,
        },
        {"handler": handler},
    )


@app.command()
def destroy(handler: str, path: str = cwd, show_logs: bool = True):
    func = import_method_from_handler(handler=handler, path=path)
    func(
        {
            "fluxional_event": "cli_destroy",
            "show_logs": show_logs,
        },
        {"handler": handler},
    )


@app.command()
def sync(handler: str, path: str = cwd):
    func = import_method_from_handler(handler=handler, path=path)
    func({"fluxional_event": "cli_sync"}, {"handler": handler})


@app.command()
def dev(handler: str, path: str = cwd):
    func = import_method_from_handler(handler=handler, path=path)
    func({"fluxional_event": "cli_dev"}, {"handler": handler})


def run_command_line():
    return app()
