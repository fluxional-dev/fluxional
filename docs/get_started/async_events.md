````python title="app.py" linenums="1"

from fluxional import Fluxional, Event, AsyncEvent, LambdaContext

flux = Fluxional("AwesomeProject")
event = Event()

@flux.event
def resize_image(event: AsyncEvent, context: LambdaContext):
    # Do something asynchronously

def run_event():
    event.trigger("resize_image", payload={...})

handler = flux.handler()

````
