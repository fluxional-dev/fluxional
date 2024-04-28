from .handlers import Handlers
from typing import Any
from .settings import Settings
from .app import App
import os
from .infrastructure.types import DynamoDBKeyT, DynamoDBLsiT, DynamoDBGsiT
from .logic import Websocket, LogicMixin, Storage, Run, Event

cwd = os.getcwd()


class Extender(LogicMixin):
    def __init__(self) -> None:
        self._settings = Settings("Extender")
        self._app = App(settings=self._settings)
        self._handlers: Handlers = Handlers(settings=self._settings, app=self._app)
        self._websocket = Websocket(app=self._app, handlers=self._handlers)
        self._storage = Storage(app=self._app, handlers=self._handlers)
        self._run = Run(app=self._app, handlers=self._handlers)
        self._event = Event(app=self._app, handlers=self._handlers)
        super().__init__(
            websocket=self._websocket,
            handlers=self._handlers,
            app=self._app,
            storage=self._storage,
            run=self._run,
            event=self._event,
        )


class Fluxional(LogicMixin):
    def __init__(
        self,
        stack_name: str,
    ) -> None:
        self._stack_name = stack_name
        self._settings = Settings(stack_name=stack_name)
        self._app = App(settings=self._settings)
        self._handlers: Handlers = Handlers(settings=self._settings, app=self._app)
        self._websocket = Websocket(app=self._app, handlers=self._handlers)
        self._storage = Storage(app=self._app, handlers=self._handlers)
        self._run = Run(app=self._app, handlers=self._handlers)
        self._event = Event(app=self._app, handlers=self._handlers)
        super().__init__(
            websocket=self._websocket,
            handlers=self._handlers,
            app=self._app,
            storage=self._storage,
            run=self._run,
            event=self._event,
        )

    @property
    def settings(self) -> Settings:
        return self._settings

    def add_dynamodb(
        self,
        *,
        partition_key: DynamoDBKeyT | None = None,
        sort_key: DynamoDBKeyT | None = None,
        remove_on_delete: bool = True,
        local_secondary_indexes: list[DynamoDBLsiT] | None = None,
        global_secondary_indexes: list[DynamoDBGsiT] | None = None,
    ) -> None:
        return self._app.add_dynamodb(
            partition_key=partition_key,
            sort_key=sort_key,
            remove_on_delete=remove_on_delete,
            local_secondary_indexes=local_secondary_indexes,
            global_secondary_indexes=global_secondary_indexes,
        )

    def configure(
        self,
        *,
        aws_account_id: str | None = None,
        aws_region: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        dependencies: list[str] = [],
        environment: dict[str, str] = {},
        requirements_file: str | None = "requirements.txt",
    ) -> None:
        """
        Configure the settings for the project
        """
        return self._settings.configure(
            aws_account_id=aws_account_id,
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            dependencies=dependencies,
            environment=environment,
            requirements_file=requirements_file,
        )

    def synth(self):
        """
        Generate the infrastructure Cloudformation template
        using cdk synth
        """
        from .infrastructure.base import Infrastructure
        from .infrastructure.resources import InfrastructureT, InfraSettings

        # Resolve environment variables by attempting to find
        # it in the os if it is not a static value
        environment = {
            k: os.environ.get(k, v)
            for k, v in self._settings.build.environment.items()
            # @REFRACTOR
            # This needs to be refractored k cannot be none here
            # If an environment variable of None is passed it will fail
            if (k, v) != (None, None)
        }
        # Resolve build environment
        build_environment = {
            k: os.environ.get(k)
            for k in self._settings.system.build_environment
            if os.environ.get(k)
        }

        infra = Infrastructure(
            infrastructure=InfrastructureT(
                settings=InfraSettings(
                    stack_name=self._stack_name,
                    aws_account_id=self._settings.credentials.aws_account_id,
                    aws_region=self._settings.credentials.aws_region,
                    environment=environment | build_environment,
                ),
                resources=self._app.build_resources(),
            )
        )

        return infra.stack().app.synth()

    def handler(self) -> Any:
        """
        Main entrypoint for all events
        """

        cli = self._handlers.synth_handler()
        if cli is not None:
            return self.synth()

        return self._handlers.handler()

    def register(self, extender: Extender) -> None:

        def _append_only(handlers: dict, extender_handlers: dict):
            for key, value in extender_handlers.items():
                if key not in handlers:
                    handlers[key] = value

        # At this point we will just override for the api
        if extender._app.api.active:
            self._app.api = extender._app.api
            self._handlers._http_handlers = extender._handlers._http_handlers

        if extender.websocket._app.websocket.routes:
            self._app.websocket = extender._app.websocket
            _append_only(
                self._handlers._websocket_handlers,
                extender._handlers._websocket_handlers,
            )

        if self._settings.storage.enable or extender._app.storage.active:
            self._app.storage = extender._app.storage
            _append_only(
                self._handlers._storage_handlers,
                extender._handlers._storage_handlers,
            )

        if extender._app.schedule.rate_schedule or extender._app.schedule.cron_schedule:
            self._app.schedule = extender._app.schedule
            _append_only(
                self._handlers._rate_schedule_handlers,
                extender._handlers._rate_schedule_handlers,
            )
            _append_only(
                self._handlers._cron_schedule_handlers,
                extender._handlers._cron_schedule_handlers,
            )

        if extender._app.event.active:
            self._app.event = extender._app.event
            _append_only(
                self._handlers._sqs_handlers,
                extender._handlers._sqs_handlers,
            )

    def set_settings(self, settings: Settings) -> None:
        settings.stack_name = self._stack_name
        self._settings = settings
        self._app.settings = settings
        self._handlers._settings = settings
