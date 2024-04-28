```python title="app.py" linenums="1"

from fluxional import Fluxional, WsEvent, LambdaContext

flux = Fluxional("AwesomeProject")

@flux.websocket.on_connect
def connect(event: WsEvent, context: LambdaContext):
    ...

@flux.websocket.on("some_action")
def on_action(event: WsEvent, context: LambdaContext):
    ...

handler = flux.handler()
```
