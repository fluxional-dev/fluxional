import os
from aws_cdk import (
    App,
    Stack,
    Environment,
)
from constructs import Construct


## AWS ACCOUNT: Account informations
ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID")
REGION = "us-east-1"
ENV = Environment(account=ACCOUNT_ID, region=REGION)

## APP INFOS
STACK_NAME = "SomeStack"


class AppStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)


app = App()
AppStack(app, STACK_NAME, env=ENV)
app.synth()
