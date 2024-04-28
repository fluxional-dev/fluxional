from typing import Any
from fluxional.types import HandlerFunctionT, AsyncHandlerFunctionT, AsyncTypeGuard
from fluxional.core.events import (
    is_http_event,
    is_fluxional_event,
    is_websocket_event,
    is_dev_context,
    is_s3_bucket_create_event,
    is_s3_bucket_delete_event,
    is_rate_schedule_event,
    is_cron_schedule_event,
    is_sqs_event,
    S3_ACTIONS,
)
from fluxional.core.app import App
from fluxional.exceptions import NoHandlerFound
from fluxional.utils import (
    default_aws_account_id,
    default_aws_region,
    default_aws_secret_access_key,
    default_aws_access_key_id,
)
from .settings import Settings
import asyncio
import sys
from uuid import uuid4
import time
import os
import json
from fluxional.core.tools import LookupKey
from .types import LambdaContext

_HandlerFunctionT = HandlerFunctionT | AsyncHandlerFunctionT


class Handlers:
    def __init__(
        self, *, settings: Settings | None = None, app: App | None = None
    ) -> None:
        self._settings = settings
        self._app = app
        self._fluxional_handlers: list[_HandlerFunctionT] = []
        self._http_handlers: list[_HandlerFunctionT] = []
        self._websocket_handlers: dict[str, _HandlerFunctionT] = {}
        self._storage_handlers: dict[str, _HandlerFunctionT] = {}
        self._rate_schedule_handlers: dict[str, _HandlerFunctionT] = {}
        self._cron_schedule_handlers: dict[str, _HandlerFunctionT] = {}
        self._sqs_handlers: dict[str, _HandlerFunctionT] = {}

    def _default_handlers(self) -> dict[str, HandlerFunctionT]:
        return {
            "deployment_handler": lambda event, context: deployment_handler(
                event, context, settings=self._settings
            ),
            "cli_dev_handler": lambda event, context: cli_dev_handler(
                event, context, settings=self._settings
            ),
        }

    def _register_default_handlers(self) -> None:
        handlers = self._default_handlers()

        for _, handler in handlers.items():
            self.add_fluxional_handler(handler)

    def add_fluxional_handler(self, handler: _HandlerFunctionT):
        self._fluxional_handlers.append(handler)

    def get_result(self, handler: _HandlerFunctionT, event, context):
        result: Any = None

        # We need to capture the exception here so that we can
        # know for unhandled errors
        exception: BaseException | None = None

        try:
            if AsyncTypeGuard.is_async(handler):
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(handler(event, context))

            else:
                result = handler(event, context)

        except Exception as e:
            exception = e

        if result is not None:
            return result

        if exception is not None:
            raise exception

    def sync_or_async(self, event, context) -> Any:

        handlers = []

        # Handler context
        if is_dev_context(event, context):
            handlers = [lambda e, c: dev_handler(e, c, settings=self._settings)]

        # Handle fluxional events
        elif is_fluxional_event(event, context):
            handlers = self._fluxional_handlers
            for handler in handlers:
                result = self.get_result(handler, event, context)
                if result:
                    return result

        # Handle http events
        elif is_http_event(event, context):
            handlers = self._http_handlers

        # Handle websocket events
        elif is_websocket_event(event, context):
            route = is_websocket_event(event, context)
            if route in self._websocket_handlers and isinstance(route, str):
                handlers = [self._websocket_handlers[route]]

        elif is_s3_bucket_create_event(event, context):
            if "create" in self._storage_handlers:
                handlers = [self._storage_handlers["create"]]

        elif is_s3_bucket_delete_event(event, context):
            if "delete" in self._storage_handlers:
                handlers = [self._storage_handlers["delete"]]

        elif is_rate_schedule_event(event, context):
            if event["schedule_name"] in self._rate_schedule_handlers:
                handlers = [self._rate_schedule_handlers[event["schedule_name"]]]

        elif is_cron_schedule_event(event, context):
            if event["schedule_name"] in self._cron_schedule_handlers:
                handlers = [self._cron_schedule_handlers[event["schedule_name"]]]

        elif is_sqs_event(event, context):
            # @TODO: Probably will need to be refractored
            body = json.loads(event["Records"][0]["body"])
            if body["event_name"] in self._sqs_handlers:
                handlers = [
                    lambda _, c: self._sqs_handlers[body["event_name"]](body["data"], c)
                ]

        if not handlers:
            raise NoHandlerFound("No handler found")

        # This may need to be refractored at some point
        handler = handlers[0]
        return self.get_result(handler, event, context)

    def synth_handler(self) -> Any:
        """Special case for when file is called directly with
        CLI - IE generating infrastructure"""

        if "--synth" in sys.argv:
            return True

    def handler(self) -> Any:
        self._register_default_handlers()
        return self.sync_or_async

    def add_api_handler(self, handler: _HandlerFunctionT) -> None:
        self._http_handlers.append(handler)

    def add_websocket_route_handler(
        self,
        route: str,
        handler: _HandlerFunctionT,
    ) -> None:
        self._websocket_handlers[route] = handler

    def add_storage_handler(
        self, action: S3_ACTIONS, handler: _HandlerFunctionT
    ) -> None:
        self._storage_handlers[action] = handler


def cli_dev_handler(event: dict, context: Any, settings: Settings | None = None):
    if not event.get("fluxional_event"):
        return None

    if event["fluxional_event"] != "cli_dev":
        return None

    if not settings:
        raise ValueError("Settings are required to run RTL.")

    from fluxional.dev import run_dev

    run_dev(
        settings.stack_name,
        handler=context["handler"],
    )

    return True


def deployment_handler(
    event: dict, context: Any, settings: Settings | None = None
) -> bool | None:
    if not event.get("fluxional_event"):
        return None

    if event["fluxional_event"] not in ["cli_deploy", "cli_destroy"]:
        return None

    if not settings:
        raise ValueError("Settings are required to deploy.")

    handler: str = context["handler"]
    show_logs: bool = event.get("show_logs", False)
    stack_name = settings.stack_name
    aws_account_id = settings.credentials.aws_account_id
    aws_region = settings.credentials.aws_region
    aws_access_key_id = settings.credentials.aws_access_key_id
    aws_secret_access_key = settings.credentials.aws_secret_access_key
    dependencies = settings.build.dependencies
    environment = settings.build.environment
    enable_otel = settings.monitoring.otel.enable
    enable_telemetry = settings.monitoring.telemetry.enable

    if settings.development.enable_local:
        # Turn on development mode
        environment[LookupKey.handler_context] = "development"

    if enable_otel:
        # Add vars necessary for otel
        environment["OTEL_EXPORTER_OTLP_ENDPOINT"] = (
            settings.monitoring.otel.exporter_otlp_endpoint
        )
        environment["OTEL_EXPORTER_OTLP_HEADERS"] = (
            settings.monitoring.otel.exporter_otlp_headers
        )

        environment["AWS_LAMBDA_EXEC_WRAPPER"] = settings.system.aws_lambda_exec_wrapper

        environment["OTEL_SERVICE_NAME"] = settings.monitoring.otel.service_name

    requirements_file = settings.build.requirements_file
    build_path = settings.build.build_path or "."
    container_command = settings.system.container_command

    from fluxional.deployment import CDKEngine

    engine = CDKEngine(
        aws_account_id=aws_account_id or default_aws_account_id(),
        aws_region=aws_region or default_aws_region(),
        aws_access_key_id=aws_access_key_id or default_aws_access_key_id(),
        aws_secret_access_key=aws_secret_access_key or default_aws_secret_access_key(),
        build_path=build_path,
        tag=f"{stack_name.lower()}_base_image",
    )

    if event["fluxional_event"] == "cli_destroy":
        engine.destroy(
            handler,
            dependencies=dependencies,
            environment=environment,
            requirements_file=requirements_file,
            command=container_command,
            lambda_handler=settings.system.lambda_handler,
            show_logs=show_logs,
        )

    else:
        engine.deploy(
            handler,
            dependencies=dependencies,
            environment=environment,
            requirements_file=requirements_file,
            command=container_command,
            lambda_handler=settings.system.lambda_handler,
            show_logs=show_logs,
            include_otel=enable_otel,
            include_fte=enable_telemetry,
        )

    return True


class _DevState:
    subscriber_id: str | None = None
    acknowledged: bool = False
    response: dict | None = None

    def to_dict(self, value: bytes) -> dict:
        return json.loads(value.decode("utf-8"))

    def acknowledge(self, **kwargs):
        if not self.acknowledged:
            self.acknowledged = True
            # Set the subscriber id
            self.subscriber_id = self.to_dict(kwargs["payload"])["subscriber_id"]

    def on_event(self, **kwargs):
        payload = self.to_dict(kwargs["payload"])
        if payload["subscriber_id"] == self.subscriber_id:
            self.response = payload["response"]


def dev_handler(
    event: dict,
    context: LambdaContext,
    settings: Settings | None = None,
    ack_timeout=15,
    timeout=15,
    state=_DevState,
):
    state = state()

    if not settings:
        raise ValueError("Settings are required to run RTL.")

    from fluxional.dev.client import DevClient

    event_id = str(uuid4())
    stack_name = settings.stack_name

    client = DevClient()
    client.connect()

    client.subscribe(f"fluxional/response/{event_id}", state.on_event)
    client.subscribe(f"fluxional/acknowledge/{event_id}", state.acknowledge)

    # execution context
    starts_with = ["AWS_", "fluxional"]
    execution_context = {
        key: value
        for key, value in dict(os.environ).items()
        if any(key.startswith(start) for start in starts_with)
    }

    pub = client.publish(
        f"fluxional/events/{stack_name}",
        {
            "type": "new_event",
            "event_id": event_id,
            "event": event,
            "execution_context": execution_context,
        },
    )

    pub.result(timeout=timeout)

    # This needs to be acknowledged by some subscriber within
    # the timeout
    start = time.time()
    while True:
        if time.time() - start > ack_timeout:
            return {"statusCode": 500, "body": "Failed to acknowledge event."}

        if state.acknowledged:
            break

    # Only http needs to wait for a response
    # The rest are async
    start = time.time()
    if is_http_event(event, context):
        # But less than timeout which is pretty long already
        while True:
            if time.time() - start > timeout:
                return {"statusCode": 500, "body": "Failed to get a response in time."}

            if state.response:
                return state.response
    else:
        return {"statusCode": 200}
