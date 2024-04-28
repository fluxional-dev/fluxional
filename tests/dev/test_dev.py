from fluxional.dev import run_dev, run_container, worker, Workers, run_forever
from unittest.mock import MagicMock
import pytest


class DevClient:
    def __init__(self, *args, **kwargs):
        self.counter = 0

    def connect(self, *_, **__):
        pass

    def close(self):
        pass

    def subscribe(self, _, func):
        pass

    def publish(self, *args, **kwargs):
        mock = MagicMock()
        mock.result.return_value = True
        return mock

    def unsubscribe(self, *args, **kwargs):
        pass

    def disconnect(self, *args, **kwargs):
        pass


def test_run_container():
    # Missing fluxional_handler_context for example in payload
    with pytest.raises(ValueError):
        run_container(
            stack_name="test",
            payload=b'{"type": "new_event", "event_id": "test", "event": {"httpMethod": "GET"}, "execution_context": {"something": "xxx"}}',
            subscriber_id="test",
        )

    run_container(
        stack_name="test",
        payload=b'{"type": "new_event", "event_id": "test", "event": {"httpMethod": "GET"}, "execution_context": {"fluxional_handler_context": {"handler": "test"}}}',
        subscriber_id="test",
        runner_function=lambda *args, **kwargs: None,
    )


def test_run_dev():
    class MockWorkers:
        def start(self):
            pass

        def stop(self):
            pass

        def add_to_queue(self, item: dict):
            pass

    run_dev(
        stack_name="test",
        handler="test",
        dev_client=DevClient,
        build_function=lambda *args, **kwargs: None,
        workers_provider=MockWorkers,
        run_forever=lambda *args, **kwargs: None,
    )


def test_worker():
    mock = MagicMock()
    mock.get.return_value = None

    # Should exist
    worker(
        queue=mock,
        worker_id=0,
        color="red",
        container_provider=lambda *args, **kwargs: None,
    )

    # Should run normally but raise error from here to exit
    # While loop

    mock = MagicMock()
    mock.task_done.side_effect = NotImplementedError

    with pytest.raises(NotImplementedError):
        worker(
            queue=mock,
            worker_id=0,
            color="red",
            container_provider=lambda *args, **kwargs: None,
        )


def test_workers():
    def worker(queue, index, color):
        while True:
            item = queue.get()
            if item is None:
                break
            # process item
            queue.task_done()

    workers = Workers(num_workers=2, worker=worker)
    # Start the workers
    workers.start()

    # Add an item to the queue
    workers.add_to_queue({"key": "value"})

    workers.queue.join()

    # Stop the workers
    workers.stop()

    # Assert that the last thread is not alive
    assert not workers.thread.is_alive()


def test_run_forever():
    loop_function = MagicMock()
    loop_function.side_effect = KeyboardInterrupt

    run_forever(
        workers=MagicMock(),
        client=MagicMock(),
        loop_function=loop_function,
    )
