from fluxional.types import HandlerFunctionT, AsyncHandlerFunctionT
from .infrastructure.types import RateDurationUnitT
from .handlers import Handlers
from .app import App
import functools


class Websocket:
    def __init__(self, app: App, handlers: Handlers) -> None:
        self._app = app
        self._handlers = handlers

    def on_connect(self, handler: HandlerFunctionT | AsyncHandlerFunctionT):
        # Add the connect route
        self._app.websocket.add_connect_route()
        # Add route to handlers
        self._handlers.add_websocket_route_handler("$connect", handler)

        return handler

    def on_disconnect(self, handler: HandlerFunctionT | AsyncHandlerFunctionT):
        # Add the disconnect route
        self._app.websocket.add_disconnect_route()
        # Add route to handlers
        self._handlers.add_websocket_route_handler("$disconnect", handler)

        return handler

    def default(self, handler: HandlerFunctionT | AsyncHandlerFunctionT):
        # Add the default route
        self._app.websocket.add_default_route()
        # Add route to handlers
        self._handlers.add_websocket_route_handler("$default", handler)

        return handler

    def on(
        self,
        route: str,
        handler: HandlerFunctionT | AsyncHandlerFunctionT | None = None,
    ):
        if handler is None:

            def decorator(handler: HandlerFunctionT | AsyncHandlerFunctionT):
                # Add the route
                self._app.websocket.add_route(route)
                # Add route to handlers
                self._handlers.add_websocket_route_handler(route, handler)

                @functools.wraps(handler)
                def wrapper(*args, **kwargs):
                    return handler(*args, **kwargs)

                return wrapper

            return decorator

        else:
            # Add the route
            self._app.websocket.add_route(route)
            # Add route to handlers
            self._handlers.add_websocket_route_handler(route, handler)
            return handler


class Storage:
    def __init__(self, app: App, handlers: Handlers) -> None:
        self._app = app
        self._handlers = handlers

    def on_upload(self, handler: HandlerFunctionT | AsyncHandlerFunctionT):
        self._app.storage.active = True
        self._handlers.add_storage_handler("create", handler)
        return handler

    def on_delete(self, handler: HandlerFunctionT | AsyncHandlerFunctionT):
        self._app.storage.active = True
        self._handlers.add_storage_handler("delete", handler)
        return handler


class Run:
    def __init__(self, app: App, handlers: Handlers) -> None:
        self._app = app
        self._handlers = handlers

    def every(self, value: int | float, unit: RateDurationUnitT):
        def decorator(handler: HandlerFunctionT | AsyncHandlerFunctionT):
            function_name = handler.__name__
            # add to app
            self._app.schedule.rate_schedule.append(
                {
                    "schedule_name": function_name,
                    "value": value,
                    "unit": unit,
                }
            )

            # Add the handler to handlers
            self._handlers._rate_schedule_handlers[function_name] = handler

            return handler

        return decorator

    def on(
        self,
        day: str | None = None,
        hour: str | None = None,
        minute: str | None = None,
        month: str | None = None,
        week_day: str | None = None,
        year: str | None = None,
    ):
        def decorator(handler: HandlerFunctionT | AsyncHandlerFunctionT):
            function_name = handler.__name__
            # add to app
            self._app.schedule.cron_schedule.append(
                {
                    "schedule_name": function_name,
                    "day": day,
                    "hour": hour,
                    "minute": minute,
                    "month": month,
                    "week_day": week_day,
                    "year": year,
                }
            )

            # Add the handler to handlers
            self._handlers._cron_schedule_handlers[function_name] = handler

            return handler

        return decorator


class Event:
    def __init__(self, app: App, handlers: Handlers) -> None:
        self._app = app
        self._handlers = handlers

    def event(
        self,
        handler: HandlerFunctionT | AsyncHandlerFunctionT,
    ):
        function_name = handler.__name__
        self._app.event.active = True
        self._handlers._sqs_handlers[function_name] = handler
        return handler


class LogicMixin:
    def __init__(
        self,
        *,
        websocket: Websocket,
        handlers: Handlers,
        app: App,
        storage: Storage,
        run: Run,
        event: Event,
    ) -> None:
        self._websocket = websocket
        self._handlers = handlers
        self._app = app
        self._storage = storage
        self._run = run
        self._event = event

    @property
    def websocket(self) -> Websocket:
        return self._websocket

    @property
    def storage(self) -> Storage:
        return self._storage

    @property
    def run(self) -> Run:
        return self._run

    def event(
        self,
        handler: HandlerFunctionT | AsyncHandlerFunctionT,
    ):
        self._event.event(handler)
        return handler

    def api(self, handler: HandlerFunctionT | AsyncHandlerFunctionT):
        self.add_api(handler)
        return handler

    def add_api(
        self,
        handler: HandlerFunctionT | AsyncHandlerFunctionT,
    ) -> None:
        """
        Add an API handler to the application
        """
        self._handlers.add_api_handler(handler)
        self._app.set_api()
