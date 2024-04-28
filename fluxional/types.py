from typing import Callable, Any, TypeGuard, Awaitable
import inspect

# Represents a lambda function style handler Accepts (event, context)
HandlerFunctionT = Callable[[Any, Any], Any]
AsyncHandlerFunctionT = Callable[[Any, Any], Awaitable[Any]]


class AsyncTypeGuard:
    @staticmethod
    def is_async(
        handler: HandlerFunctionT | AsyncHandlerFunctionT,
    ) -> TypeGuard[AsyncHandlerFunctionT]:
        return inspect.iscoroutinefunction(handler)
