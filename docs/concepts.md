<b class="theme-primary-light">Fluxional</b> is an abstraction layer over commonly used aws libraries such as <u>Boto3 and AWS CDK</u>. It provides a simple and intuitive interface to create and deploy serverless applications on AWS.<br>

### 1) The setup phase

Minimal Host Dependencies and No managing versions of iac, nodes, cli etc... all in docker with a single command.

Provide your credentials directly to fluxional and it will take care of the rest in a container.

```python
from fluxional import Fluxional

fluxional = Fluxional("Backend")

# All of these are automatically fetched from your .env file
fluxional.configure(
    aws_account_id=...,
    aws_region=...,
    aws_access_key_id=...,
    aws_secret_access_key=...,
)

```

---

### 2) The dev phase

Let's look at deploying a simple Rest-API that returns hello world

=== "The fluxional way"

    <b>One file</b> is all you need

    ```python

    from fluxional import Fluxional, ApiEvent, LambdaContext

    flx = Fluxional("Backend")

    @flx.api
    def hello(event: ApiEvent, context: LambdaContext):
        return {"statusCode": 200, "body": "Hello World"}

    handler = flx.handler()

    ```

=== "The traditional way"

    Write your handler

    ```python

    def handler(event: ApiEvent, context: LambdaContext):
        return {"statusCode": 200, "body": "Hello World"}

    ```

    Write your dockerfile

    ```dockerfile
    FROM public.ecr.aws/lambda/python:3.10

    COPY app.py requirements.txt ./

    RUN pip install -r requirements.txt -t .

    CMD ["app.handler"]

    ```

    Write your IAC

    ```python
    from aws_cdk import ...

    lambda_function = aws_lambda.Function(
            self,
            id=SERVICE_NAME + "_lambda",
            description=SERVICE_NAME + "_lambda",
            code=ecr_image,
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            function_name=SERVICE_NAME,
            memory_size=128,
            timeout=Duration.seconds(900),
        )

    # ETC...
    ```

---

### 3-4-5) Testing, Deployment, Testing...

We have all been there, unit tests work, integration tests with local mocks works, we deploy and wait for a minute.
And then an unexpected error occurs such as say Cors, forgotten permissions. <br> <br>Now we wait for another minute to deploy
and so on and so forth. Fluxional accelerate this by allowing to develop with a live lambda with the exact environment. This work
is inspired by the developers at [sst](https://docs.sst.dev/live-lambda-development).
