from fluxional.core.handlers import (
    Handlers,
    deployment_handler,
    cli_dev_handler,
    dev_handler,
    _DevState,
)
from fluxional.core.settings import Settings
from fluxional.exceptions import NoHandlerFound
import asyncio
import pytest
from unittest.mock import patch
import os
from fluxional.core.tools import LookupKey


def test_a_failed_handler_exception():
    handler = Handlers()
    handler.add_api_handler(lambda *a, **b: 1 / 0)  # noqa

    with pytest.raises(ZeroDivisionError):
        handler.handler()({"httpMethod": "GET"}, {})


def test_sync_handler():
    handler = Handlers()

    def sync_handler(event, context):
        return "sync"

    handler._http_handlers = [sync_handler]

    assert handler.handler()({"httpMethod": "GET"}, None) == "sync"


def test_async_handler():
    async def x(event, context):
        if "async" in event:
            events = []

            async def slow_event():
                await asyncio.sleep(0.1)
                events.append("slow")

            async def fast_event():
                events.append("fast")

            await asyncio.gather(slow_event(), fast_event())

            return events
        return

    handler = Handlers()

    handler._http_handlers = [x]

    assert handler.handler()({"async": True, "httpMethod": "GET"}, {}) == [
        "fast",
        "slow",
    ]


def test_default_fluxional_handlers():
    handler = Handlers()

    handler._fluxional_handlers = [lambda event, context: "fluxional"]

    assert handler.handler()({"fluxional_event": "cli_deploy"}, {}) == "fluxional"


def test_error_when_no_handler_found():
    with pytest.raises(NoHandlerFound):
        handler = Handlers()

        handler.handler()({}, {})


def test_add_handler():
    handler = Handlers()
    x = lambda event, context: "sync"  # noqa
    handler._fluxional_handlers = []  # Reset the default ones
    handler.add_api_handler(x)
    handler.add_fluxional_handler(x)

    assert handler._http_handlers
    assert handler._fluxional_handlers


def test_that_default_handlers_are_registered():
    handler = Handlers()

    handler.handler()

    assert handler._fluxional_handlers


def test_add_api_handler():
    handler = Handlers()

    def sync_handler(event, context):
        return "sync"

    handler.add_api_handler(sync_handler)

    assert handler.handler()({"httpMethod": "GET"}, {}) == "sync"

    handler = Handlers()

    async def async_handler(event, context):
        return "async"

    handler.add_api_handler(async_handler)

    assert handler.handler()({"httpMethod": "GET"}, {}) == "async"


def test_deployment_handler():
    # not a valid event
    assert deployment_handler({}, {}) is None
    assert deployment_handler({"fluxional_event": "not_valid"}, {}) is None

    # Fails if not a valid settings
    with pytest.raises(ValueError):
        deployment_handler(
            {"fluxional_event": "cli_deploy"}, {"handler": "app.handler"}
        )

    # Fails if any of aws_account_id, aws_region, aws_access_key_id, aws_secret_access_key are missing
    settings = Settings(
        stack_name="SomeStack",
    )

    settings.credentials.aws_account_id = "123456789012"

    with pytest.raises(ValueError):
        deployment_handler(
            {"fluxional_event": "cli_deploy"},
            {"handler": "app.handler"},
            settings=settings,
        )

    settings = Settings(
        stack_name="SomeStack",
    )

    settings.credentials.aws_account_id = "123456789012"
    settings.credentials.aws_region = "us-east-1"

    with pytest.raises(ValueError):
        deployment_handler(
            {"fluxional_event": "cli_deploy"},
            {"handler": "app.handler"},
            settings=settings,
        )

    settings = Settings(
        stack_name="SomeStack",
    )

    settings.credentials.aws_account_id = "123456789012"
    settings.credentials.aws_region = "us-east-1"
    settings.credentials.aws_access_key_id = "123456789012"

    with pytest.raises(ValueError):
        deployment_handler(
            {"fluxional_event": "cli_deploy"},
            {"handler": "app.handler"},
            settings=settings,
        )

    settings = Settings(
        stack_name="SomeStack",
    )

    settings.credentials.aws_account_id = "123456789012"
    settings.credentials.aws_region = "us-east-1"
    settings.credentials.aws_access_key_id = "123456789012"

    with pytest.raises(ValueError):
        deployment_handler(
            {"fluxional_event": "cli_deploy"},
            {"handler": "app.handler"},
            settings=settings,
        )

    settings = Settings(
        stack_name="SomeStack",
    )

    settings.development.enable_local = True

    settings.build.build_path = "tests/core/"
    settings.build.requirements_file = "mock_req.txt"
    settings.credentials.aws_account_id = "123456789012"
    settings.credentials.aws_region = "us-east-1"
    settings.credentials.aws_access_key_id = "123456789012"
    settings.credentials.aws_secret_access_key = "123456789012"
    settings.system.container_command = "cdk --version"
    settings.monitoring.otel.enable = True

    assert deployment_handler(
        {"fluxional_event": "cli_destroy"},
        {"handler": "mock_app.handler"},
        settings=settings,
    )

    assert deployment_handler(
        {"fluxional_event": "cli_deploy"},
        {"handler": "mock_app.handler", "development": True},
        settings=settings,
    )


def test_adding_websocket_routes():
    handler = Handlers(settings=Settings(stack_name="SomeStack"))

    handler.add_websocket_route_handler(
        "$connect",
        lambda *a, **b: "websocket",
    )

    assert handler._websocket_handlers["$connect"]

    assert (
        handler.handler()(  # noqa
            {
                "requestContext": {
                    "routeKey": "$connect",
                }
            },
            {},
        )
        == "websocket"
    )


def test_cli_dev_handler():
    # returns none if not a valid event
    assert cli_dev_handler({}, {}) is None
    assert cli_dev_handler({"fluxional_event": "not_valid"}, {}) is None

    # Missing settings
    with pytest.raises(ValueError):
        cli_dev_handler(
            {"fluxional_event": "cli_dev"},
            {},
        )

    settings = Settings(
        stack_name="SomeStack",
    )

    settings.development.enable_local = True

    with patch("fluxional.dev.run_dev", return_value=None):
        cli_dev_handler(
            {"fluxional_event": "cli_dev"},
            {"handler": "mock_app.handler"},
            settings=settings,
        )


def test_dev_handler():
    # The correct handler should be triggered

    state = _DevState()
    assert state.to_dict(
        b'{"type": "new_event", "event_id": "test", "event": {"httpMethod": "GET"}, "execution_context": {"something": "xxx"}}'
    ) == {
        "event": {"httpMethod": "GET"},
        "event_id": "test",
        "execution_context": {"something": "xxx"},
        "type": "new_event",
    }
    state.acknowledge(payload=b'{"subscriber_id": "123"}')
    assert state.acknowledged

    state.on_event(payload=b'{"subscriber_id": "123", "response": {"statusCode": 200}}')
    assert state.response == {"statusCode": 200}

    class DevClient:
        def __init__(self, *args, **kwargs):
            pass  # Add any setup code for your mock class here

        def connect(self, *_, **__):
            pass

        def close(self):
            pass

        def subscribe(self, *args, **kwargs):
            pass

        def publish(self, *args, **kwargs):
            class Mock:
                def result(*args, **kwargs):
                    pass

            return Mock()

        def unsubscribe(self, *args, **kwargs):
            pass

    settings = Settings(
        stack_name="SomeStack",
    )

    # No settings
    with pytest.raises(ValueError):
        req = dev_handler(
            {
                "httpMethod": "GET",
            },
            {},
        )

    with patch("fluxional.dev.client.DevClient", new=DevClient):
        req = dev_handler(
            {
                "httpMethod": "GET",
            },
            {},
            settings,
            ack_timeout=0.1,
        )

        assert req["statusCode"] == 500
        assert req["body"] == "Failed to acknowledge event."

        state = _DevState
        state.acknowledged = True

        req = dev_handler(
            {
                "httpMethod": "GET",
            },
            {},
            settings,
            ack_timeout=0.1,
            timeout=0.1,
            state=state,
        )

        assert req["statusCode"] == 500
        assert req["body"] == "Failed to get a response in time."

        # with response it returns the response
        state = _DevState
        state.acknowledged = True
        state.response = {"statusCode": 200, "body": "response"}

        req = dev_handler(
            {
                "httpMethod": "GET",
            },
            {},
            settings,
            ack_timeout=0.1,
            timeout=0.1,
            state=state,
        )

        assert req["statusCode"] == 200
        assert req["body"] == "response"

        # Any other method but http should be async and return 200

        req = dev_handler(
            {
                "sns": "stuff",
            },
            {},
            settings,
            ack_timeout=0.1,
            timeout=0.1,
            state=state,
        )

        assert req["statusCode"] == 200

        # Test that dev handler is called properly whe the context is write

        with patch.object(os, "environ", {LookupKey.handler_context: "development"}):
            handler = Handlers(settings=settings)
            handler.handler()({"httpMethod": "GET"}, {})
