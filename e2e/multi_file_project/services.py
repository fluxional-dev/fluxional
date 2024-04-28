from fluxional import Extender, ApiEvent, LambdaContext, WsEvent, StorageEvent
from typing import Any

flux = Extender()


## API ##
@flux.api
def hello_world(event: ApiEvent, context: LambdaContext):
    return {"statusCode": 200, "body": "Hello, World!"}


## Websocket ##
@flux.websocket.on_connect
def on_connect(event: WsEvent, context: LambdaContext):
    return {"statusCode": 200}


## Async Events ##
@flux.event
def say_hello(event: Any, context: LambdaContext):
    return {"statusCode": 200}


## Storage ##
@flux.storage.on_upload
def on_upload(event: StorageEvent, context: LambdaContext):
    return {"statusCode": 200}


## Tasks ##
@flux.run.every(1, "minutes")
def every_minute(event: Any, context: LambdaContext):
    return {"statusCode": 200}
