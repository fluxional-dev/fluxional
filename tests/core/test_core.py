from fluxional import Fluxional, Settings
from fluxional.core.infrastructure.resources import (
    LambdaFunction,
    DynamoDB,
    ApiGateway,
    DynamoDbPermission,
    SnsTopic,
    S3Bucket,
)
from unittest.mock import patch, Mock
import sys


def test_fluxional_handler():
    fluxional = Fluxional("Test")
    assert fluxional._stack_name == "Test"

    handler = lambda event, context: "sync"  # noqa

    fluxional.add_api(handler)

    assert fluxional.handler()({"httpMethod": "GET"}, {}) == "sync"


def test_fluxional_settings(stack_name="SomeStack"):
    fluxional = Fluxional("Test")

    fluxional.configure(
        aws_account_id="1234567890",
        aws_region="us-east-1",
        aws_access_key_id="1234567890",
        aws_secret_access_key="1234567890",
    )

    assert fluxional._settings.credentials.aws_account_id == "1234567890"
    assert fluxional._settings.credentials.aws_region == "us-east-1"
    assert fluxional._settings.credentials.aws_access_key_id == "1234567890"
    assert fluxional._settings.credentials.aws_secret_access_key == "1234567890"


def test_fluxional_cli_args():
    fluxional = Fluxional("Test")

    fluxional.synth = lambda: "something"

    with patch.object(sys, "argv", ["--synth"]):
        assert fluxional.handler() == "something"


def test_fluxional_generate_infratructure():
    fluxional = Fluxional("Test")
    fluxional.configure(
        aws_account_id="1234567890",
        aws_region="us-east-1",
        aws_access_key_id="1234567890",
        aws_secret_access_key="1234567890",
    )

    # This will fail because it cant find the dockerfile
    fluxional.add_api(lambda x, y: "any")

    # We need to override the lambda
    fluxional.add_api(
        lambda x, y: "any",
    )
    fluxional._settings.build.api_lambda.dockerfile = "tests/core/Dockerfile.lambda"

    assert fluxional.synth()


def test_fluxional_add_api():
    fluxional = Fluxional("Test")

    fluxional.add_api(
        lambda x, y: "any",
    )

    fluxional._settings.build.api_lambda.dockerfile = "tests/core/Dockerfile.lambda"

    resources = fluxional._app.build_resources()

    assert isinstance(
        resources[fluxional._settings.system.default_api_lambda_id], LambdaFunction
    )
    assert isinstance(resources["fluxional_api_gateway"], ApiGateway)


def test_fluxional_add_dynamodb():
    # Make sure dynamodb is in resource
    fluxional = Fluxional("Test")

    fluxional.add_dynamodb()

    fluxional.add_api(
        lambda x, y: "any",
    )

    fluxional._settings.build.api_lambda.dockerfile = "tests/core/Dockerfile.lambda"
    fluxional._settings.permissions.allow_api_to_read_from_db = True

    resources = fluxional._app.build_resources()

    assert isinstance(resources["fluxional_dynamodb"], DynamoDB)

    assert isinstance(
        resources[fluxional._settings.system.default_api_lambda_id].permissions[0],
        DynamoDbPermission,
    )


def test_websocket():
    flux = Fluxional("Test")

    func = lambda x, y: "any"  # noqa
    flux.websocket.on_connect(func)
    flux.websocket.on_disconnect(func)
    flux.websocket.default(func)
    flux.websocket.on("message", func)

    assert flux._app.websocket.routes == [
        "$connect",
        "$disconnect",
        "$default",
        "message",
    ]
    assert flux._handlers._websocket_handlers == {
        "$connect": func,
        "$disconnect": func,
        "$default": func,
        "message": func,
    }


def test_websocket_decorator():
    flux = Fluxional("Test")
    mock_handler = Mock()

    @flux.websocket.on_connect
    def test_on_connect(event, context):
        return "connect"

    @flux.websocket.on_disconnect
    def test_on_disconnect(event, context):
        return "disconnect"

    @flux.websocket.default
    def test_default(event, context):
        return "default"

    @flux.websocket.on("message")
    def test_message(event, context):
        mock_handler()
        return "any"

    assert test_message({}, {}) == "any"
    mock_handler.assert_called_once()

    assert flux._app.websocket.routes == [
        "$connect",
        "$disconnect",
        "$default",
        "message",
    ]

    # Test that functions can be called properly
    assert flux.handler()({"requestContext": {"routeKey": "$connect"}}, {}) == "connect"
    assert (
        flux.handler()({"requestContext": {"routeKey": "$disconnect"}}, {})
        == "disconnect"
    )
    assert flux.handler()({"requestContext": {"routeKey": "$default"}}, {}) == "default"
    assert flux.handler()({"requestContext": {"routeKey": "message"}}, {}) == "any"


def test_api_decorator():
    flux = Fluxional("Test")

    @flux.api
    def test_api(event, context):
        return "any"

    assert flux.handler()({"httpMethod": "GET"}, {}) == "any"
    assert test_api({}, {}) == "any"


def test_storage_decorator():
    flux = Fluxional("Test")

    @flux.storage.on_upload
    def test_on_create(event, context):
        return "create"

    @flux.storage.on_delete
    def test_on_delete(event, context):
        return "delete"

    assert (
        flux.handler()(
            {"Records": [{"eventName": "ObjectCreated:Put", "eventSource": "aws:s3"}]},
            {},
        )
        == "create"
    )
    assert (
        flux.handler()(
            {
                "Records": [
                    {"eventName": "ObjectRemoved:Delete", "eventSource": "aws:s3"}
                ]
            },
            {},
        )
        == "delete"
    )
    assert test_on_create({}, {}) == "create"
    assert test_on_delete({}, {}) == "delete"


def test_rate_schedule_decorator():
    flux = Fluxional("Test")

    @flux.run.every(1, "minutes")
    def test_every(event, context):
        return "any"

    assert test_every({}, {}) == "any"
    assert (
        flux.handler()(
            {"schedule_type": "RateSchedule", "schedule_name": "test_every"}, {}
        )
        == "any"
    )


def test_cron_schedule_decorator():
    flux = Fluxional("Test")

    @flux.run.on(day="1", hour="1", minute="1")
    def test_on(event, context):
        return "any"

    assert test_on({}, {}) == "any"
    assert (
        flux.handler()(
            {"schedule_type": "CronSchedule", "schedule_name": "test_on"}, {}
        )
        == "any"
    )


def test_event_decorator():
    flux = Fluxional("Test")

    @flux.event
    def test_on_event(event, context):
        return "any"

    assert test_on_event({}, {}) == "any"
    assert (
        flux.handler()(
            {
                "Records": [
                    {
                        "eventSource": "aws:sqs",
                        "body": '{"event_name": "test_on_event", "data": {"payload": "any"}}',
                    }
                ]
            },
            {},
        )
        == "any"
    )


def test_settings():
    flux = Fluxional("Test")

    assert isinstance(flux.settings, Settings)
