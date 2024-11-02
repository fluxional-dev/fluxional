# 🚀 AWS Serverless Development All In Python 🐍

#### This is a work in progress. If you have any questions or need help, please reach out to us.

<b class="theme-primary-light">Fluxional</b> is designed to simplify the development and deployment of serverless applications on AWS with <u>minimal</u> configuration.<br>

Key features:<br>

- Simplified infrastructure syntax
- Deployment only require credentials and docker
- Live interaction with your cloud application as you code
- Focused on developer experience with intuitive syntax and editor / type support
  <br>

Get started with:

```bash

pip install fluxional

```

<div class="index-title">1) Infrastructure is <u>simplified</u> and <u>part</u> of your code</div><br>

😎 Rest API

```python
from fluxional import Fluxional, ApiEvent, LambdaContext

flux = Fluxional("Backend")

@flux.api
def my_api(event: ApiEvent, context: LambdaContext):
    return {"statusCode": 200, "body": "ok"}

handler = flux.handler()
```

📲 Websockets

```python
from fluxional import Fluxional, WsEvent, LambdaContext, Websocket

flux = Fluxional("Backend")

@flux.websocket.on_connect
def connect(event: WsEvent, context: LambdaContext):
    return {"statusCode": 200}

@flux.websocket.on("some_action")
def on_action(event: WsEvent, context: LambdaContext):
    # Reply to the sender
    Websocket.post_to_connection(event, "Hello World!")

handler = flux.handler()
```

🔐 Databases

```python
from fluxional import Fluxional

flux = Fluxional("Backend")

flux.add_dynamodb() # 👈 This will create a dynamodb
```

🪣 Storage (S3)

```python
from fluxional import Fluxional, StorageEvent, LambdaContext

flux = Fluxional("Backend")

@flux.storage.on_upload
def on_upload(event: StorageEvent, context: LambdaContext):
    # Do something when a file is uploaded

handler = flux.handler()
```

🚶 Async Events

```python
from fluxional import Fluxional, LambdaContext, Event

flux = Fluxional("Backend")

event = Event[str]()

@flux.event
def on_event(payload: str, context: LambdaContext):
    # Do something when an event is triggered

def trigger_event():
    # Trigger on_event with str payload
    event.trigger("on_event", "Hello World!")

handler = flux.handler()
```

🕵️ Tasks

```python
from fluxional import Fluxional, TaskEvent, LambdaContext

flux = Fluxional("Backend")

@flux.run.every(1, "days")
def task_1(event: TaskEvent, context: LambdaContext):
    # Do something every day from now

handler = flux.handler()
```

<br>
<div class="index-title"> 2) Deploy <u>without installing</u> and managing Node, Aws Cli & CDK versions</div>

- Fluxional provides a containarized <b>deployment</b> flow. No need to install and Manage versions of Node, AWS Cli or CDK on your machine ⛔.
  Provide your credentials in a <b>.env</b> and you are good to go 😊.<br>

- Your AWS Lambda functions are <b>containerized</b> and <b>dockerfiles</b> are <b>auto-generated</b> 😎 based on the runtime, requirements and dependencies you need.

To deploy 🚀 your application:

<div>

```bash
$ fluxional deploy app.handler
```

</div>
To remove 🔨 your application:

<div>

```bash
$ fluxional destroy app.handler
```

</div>

<br>

<div class="index-title"> 3) <u>Live Development</u>- Interact with your microservice as you code </div>

- Invoke your microservice locally 💻 and make live changes 🕘 without the need to mock your services or re-deploy.
- Your code will be ran in a local container with the exact ✨ environment and behaviors your application will have in the cloud.

\*\* Setting must be <u>enabled</u> and <u>deployed</u> before executing below <br>

<div>

```bash
$ fluxional dev app.handler
```

</div>

<br>
