import json
from rich import print as rp
from rich.console import Console
from .client import DevClient
from uuid import uuid4
from typing import Any, Callable
from .runner import run, build_runner_image
import queue as q
import threading
from dataclasses import dataclass
from fluxional.core.tools import LookupKey


def run_container(
    *,
    stack_name: str,
    payload: Any,
    subscriber_id: str,
    runner_function: Callable = run,
):
    try:
        payload = json.loads(payload.decode("utf-8"))
        event_id = payload["event_id"]
        event = payload["event"]
        execution_context = payload["execution_context"]
        del execution_context[LookupKey.handler_context]

    except KeyError as e:
        raise ValueError(f"{e} is required in payload")

    container = runner_function(
        stack_name,
        environment={
            "EVENT_ID": event_id,
            "EVENT": json.dumps(event),
            "SUBSCRIBER_ID": subscriber_id,
            "PYTHONUNBUFFERED": "1",
            **execution_context,
        },
    )
    return container


def worker(
    queue: q.Queue, worker_id, color: str, container_provider: Callable = run_container
):
    console = Console(style=color)
    while True:
        item = queue.get()
        if item is None:
            break

        console.print(f"Worker: {worker_id} working on item queue")
        container_provider(
            stack_name=item["stack_name"],
            payload=item["kwargs"]["payload"],
            subscriber_id=item["subscriber_id"],
        )

        queue.task_done()


@dataclass
class Workers:
    num_workers: int = 5
    colors = ["red", "green", "blue", "yellow", "magenta"]
    queue: q.Queue[Any] = q.Queue[Any]()
    thread: threading.Thread | None = None
    worker: Callable = worker

    def start(self):
        assert len(self.colors) >= self.num_workers, "Not enough colors for workers"
        for i in range(self.num_workers):
            t = threading.Thread(
                target=self.worker,
                args=(self.queue, i, self.colors[i % len(self.colors)]),
            )
            t.start()
            self.thread = t

    def stop(self):
        self.queue.join()
        for _ in range(self.num_workers):
            self.queue.put(None)
        if self.thread:
            self.thread.join()

    def add_to_queue(self, item: dict):
        self.queue.put(item)


def run_forever(
    workers: Workers, client: DevClient, loop_function: Callable | None = None
):
    try:
        while True:
            if loop_function:
                loop_function()

    except KeyboardInterrupt:
        pass

    finally:
        workers.stop()
        rp("Disconnecting from server")
        client.disconnect()


def run_dev(
    stack_name: str,
    *,
    handler: str,
    dev_client: type[DevClient] = DevClient,
    build_function: Callable = build_runner_image,
    workers_provider: type[Workers] = Workers,
    run_forever: Callable = run_forever,
):
    subscriber_id = str(uuid4())

    rp("\n[bold blue]Starting Development[/bold blue]")
    client: DevClient = dev_client()

    client.connect()

    rp("[blue]Building Dev Environment[/blue]")
    build_function(stack_name, handler)

    rp("[green]Starting workers[/green]")
    workers = workers_provider()
    workers.start()

    client.subscribe(
        f"fluxional/events/{stack_name}",
        lambda **rest: workers.add_to_queue(
            {"stack_name": stack_name, "subscriber_id": subscriber_id, "kwargs": rest}
        ),
    )

    rp("[green]Connected To Server - Ready to receive events[/green]")

    run_forever(workers, client)
