from fluxional import Fluxional, Environment, WsEvent, LambdaContext, Websocket

flux = Fluxional("FluxE2EWebsocket")

flux.settings.build.websocket.stage_name = "dev"
flux.settings.build.websocket.auto_deploy = True


@flux.websocket.on_connect
def on_connect(event: WsEvent, context: LambdaContext):
    # Only on-connect and on-disconnect events have the headers and such
    print(event["headers"])
    print(event["multiValueHeaders"])
    print(event["isBase64Encoded"])
    # check env
    env = Environment()
    print(env.websocket_api_id)
    print(env.websocket_stage_name)

    return {
        "statusCode": 200,
    }


@flux.websocket.on("hello")
def hello(event: WsEvent, context: LambdaContext):
    print(event["requestContext"])
    print(event["body"])
    Websocket.post_to_connection(event, "Hello from the server!")
    return {"statusCode": 200}


@flux.websocket.on_disconnect
def on_disconnect(event: WsEvent, context: LambdaContext): ...


handler = flux.handler()
