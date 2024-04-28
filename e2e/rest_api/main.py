from fluxional import Fluxional, ApiEvent, LambdaContext, Environment


# NOTE: Cors is not handled by Fluxional - All request will be allowed
# It must be handled by either a framework or manually.


flux = Fluxional("FluxE2ERestAPI")

# Api Gateway Settings
flux.settings.build.api_gateway.stage_name = "v1"
flux.settings.build.api_gateway.description = "fluxional_api_gateway_v1"

# Lambda Settings
flux.settings.build.api_lambda.description = "fluxional_api_lambda_v1"
flux.settings.build.api_lambda.memory_size = 512


@flux.api
def hello_world(event: ApiEvent, context: LambdaContext):

    # Environment
    env = Environment()
    print(env.api_path_prefix)

    # Event
    print(event["body"])
    print(event["headers"])
    print(event["httpMethod"])
    print(event["isBase64Encoded"])
    print(event["multiValueHeaders"])
    print(event["multiValueQueryStringParameters"])
    print(event["path"])
    print(event["pathParameters"])
    print(event["queryStringParameters"])
    print(event["requestContext"])
    print(event["resource"])
    print(event["stageVariables"])

    # Context
    print(context.function_name)
    print(context.function_version)
    print(context.invoked_function_arn)
    print(context.memory_limit_in_mb)
    print(context.aws_request_id)
    print(context.log_group_name)
    print(context.log_stream_name)
    print(context.identity)
    print(context.client_context)
    print(context.get_remaining_time_in_millis())

    return {"statusCode": 200, "body": "Hello, World!"}


handler = flux.handler()
