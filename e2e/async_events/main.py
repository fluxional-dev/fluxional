from fluxional import Fluxional, Event, ApiEvent, LambdaContext
from typing import TypedDict


class Message(TypedDict):
    message: str


class PayloadType(TypedDict):
    payload: Message


flux = Fluxional("FluxE2EAsyncEvents")
# Settings
flux.settings.build.event_lambda.description = "Fluxional Async Events"
flux.settings.build.event_lambda.memory_size = 512
flux.settings.build.event_lambda.timeout = 60
flux.settings.permissions.allow_api_to_run_events = True
# Trigger
event = Event[PayloadType]()


@flux.event
def hello(payload: PayloadType, context: LambdaContext):
    print("Hello Event Triggered!")
    print(payload)


@flux.api
def trigger_event(api_event: ApiEvent, context: LambdaContext):
    event.trigger(
        "hello",
        {"payload": {"message": "Some data here!"}},
    )
    return {"statusCode": 200, "body": "Event Triggered!"}


handler = flux.handler()
