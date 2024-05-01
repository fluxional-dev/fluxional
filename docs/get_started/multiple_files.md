```python title="api.py"

from fluxional import Extender, ApiEvent, LambdaContext

flux = Extender()

@flux.api
def api_event(event: ApiEvent, context: LambdaContext):
    return {"statusCode": 200}

```

```python title="main.py"

from fluxional import Fluxional
from api import flux as api_flux

flux = Fluxional("AwesomeProject")

flux.configure(
    dependencies=["api.py"] # include the api file
)
flux.register(api_flux) # register the resource

handler = flux.handler()

```
