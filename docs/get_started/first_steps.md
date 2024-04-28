The first step in using fluxional is to create a main entry file in this case we will create an <b>app.py</b> file and import
Fluxional. Next, declare an instance of the app with a <b>unique id</b> (CamelCase) across the aws account, in this case "GetStarted":

```python title="app.py"
from fluxional import Fluxional

flux = Fluxional("GetStarted")
```

Now you can start to define your services using decorators; in this case a rest api. This will generate at deployment time
an api gateway and a lambda function integration and everything in between.

```python title="app.py"
from fluxional import Fluxional, ApiEvent, LambdaContext

flux = Fluxional("GetStarted")

@flux.api
def my_api(event: ApiEvent, context: LambdaContext):
    return {"statusCode": 200, "body": "ok"}
```

Then once finished we need to include our entrypoint handler

```python title="app.py"
from fluxional import Fluxional, ApiEvent, LambdaContext

flux = Fluxional("GetStarted")

@flux.api
def my_api(event: ApiEvent, context: LambdaContext):
    return {"statusCode": 200, "body": "ok"}

handler = flux.handler()
```

Create a <b>.env</b> file containing the following variables:

    AWS_ACCESS_KEY_ID=...
    AWS_SECRET_ACCESS_KEY=...
    AWS_DEFAULT_REGION=...
    AWS_ACCOUNT_ID=...

Put your dependencies in a "requirements.txt" in your root folder, your project should now look like this<br>

    ├── app.py
    ├── .env
    ├── requirements.txt

To deploy your application run the following command by pointing to the handler:

<div class="bash-code">

```bash
$ fluxional deploy app.handler
```

</div>

And voilà! Your application is now deployed and ready to use. Lookout for the output url in the console.
