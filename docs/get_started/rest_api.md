All HTTP requests ✈️ will be proxied to your functions, so you have the freedom to implement
any framework 🎉 that you want.

#### Example

=== "As Decorator"

    ```python title="app.py" linenums="1"
    from fluxional import Fluxional, ApiEvent, LambdaContext

    flux = Fluxional("MyApp")

    @flux.api
    def hello_world(event: ApiEvent, context: LambdaContext):
        return {"statusCode": 200, "body": "Hello World"}

    handler = flux.handler()
    ```

=== "As Inline"

    ```python title="app.py" linenums="1"
    from fluxional import Fluxional, ApiEvent, LambdaContext

    flux = Fluxional("MyApp")

    def hello_world(event: ApiEvent, context: LambdaContext):
        return {"statusCode": 200, "body": "Hello World"}

    flux.add_api(hello_world)

    handler = flux.handler()
    ```

#### Settings

You can modify your lambda and api gateway settings 🛠️ through the settings property.
By default 🤗 Fluxional will always use the <u>minimum settings</u> required to deploy 🚀 your application.

```python title="app.py" linenums="1"
from fluxional import Fluxional

flux = Fluxional("MyApp")
settings = flux.settings.build

settings.api_lambda.memory_size = 128
settings.api_lambda.timeout = 30
settings.api_lambda.description = "My lambda function"

settings.api_gateway.stage_name = "dev"
settings.api_gateway.description = "My api gateway"
settings.api_gateway.deploy = True
settings.api_gateway.endpoint_type = "regional"

```
