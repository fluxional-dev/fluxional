from aws_cdk import (
    Stack,
    aws_lambda,
    Duration,
    aws_apigateway,
    aws_dynamodb,
    RemovalPolicy,
    aws_sns,
    aws_s3,
    aws_events,
    aws_sqs,
    CfnOutput,
)
from typing import Literal
from .types import (
    DynamoDBAttributeTypeT,
    DynamoDBKeyT,
    DynamoDBLsiT,
    DynamoDBBillingModeT,
    DynamoDBStreamT,
    DynamoDBGsiT,
)
import aws_cdk.aws_apigatewayv2_alpha as aws_apigateway_v2
from .types import RateDurationUnitT


def add_rate_schedule_to_stack(
    *,
    stack: Stack,
    id: str,
    unit: RateDurationUnitT,
    value: int | float,
    schedule_name: str,
) -> aws_events.Rule:
    durations = {
        "days": Duration.days,
        "hours": Duration.hours,
        "minutes": Duration.minutes,
        "seconds": Duration.seconds,
        "milliseconds": Duration.millis,
    }

    rule = aws_events.Rule(
        stack, schedule_name, schedule=aws_events.Schedule.rate(durations[unit](value))
    )

    setattr(stack, id, rule)

    return rule


def add_cron_schedule_to_stack(
    *,
    stack: Stack,
    id: str,
    schedule_name: str,
    day: str | None,
    hour: str | None,
    minute: str | None,
    month: str | None,
    week_day: str | None,
    year: str | None,
) -> aws_events.Rule:
    rule = aws_events.Rule(
        stack,
        schedule_name,
        schedule=aws_events.Schedule.cron(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            year=year,
            week_day=week_day,
        ),
    )

    setattr(stack, id, rule)

    return rule


def add_lambda_function_to_stack(
    *,
    stack: Stack,
    id: str,
    function_name: str,
    directory: str,
    file: str,
    memory_size: int,
    timeout: int,
    description: str,
) -> aws_lambda.Function:
    ecr_image = aws_lambda.EcrImageCode.from_asset_image(directory=directory, file=file)

    lambda_function = aws_lambda.Function(
        stack,
        id=id,
        description=description,
        code=ecr_image,
        handler=aws_lambda.Handler.FROM_IMAGE,
        runtime=aws_lambda.Runtime.FROM_IMAGE,
        function_name=function_name,
        memory_size=memory_size,
        timeout=Duration.seconds(timeout),
        log_format=aws_lambda.LogFormat.JSON.value,
    )

    setattr(stack, id, lambda_function)

    return lambda_function


def add_ws_gateway_to_stack(
    *,
    stack: Stack,
    id: str,
    stage_name: str,
    websocket_name: str,
    auto_deploy: bool,
) -> aws_apigateway_v2.WebSocketApi:
    web_socket_api = aws_apigateway_v2.WebSocketApi(stack, id, api_name=websocket_name)
    aws_apigateway_v2.WebSocketStage(
        stack,
        id + "_stage",
        web_socket_api=web_socket_api,
        stage_name=stage_name,
        auto_deploy=auto_deploy,
    )

    # Output the websocket url
    CfnOutput(
        stack,
        "WebsocketUrl",
        value=f"{web_socket_api.api_endpoint}/{stage_name}",
        description="The URL of the websocket",
    )

    setattr(stack, id, web_socket_api)

    return web_socket_api


def add_rest_api_gateway_to_stack(
    *,
    stack: Stack,
    id: str,
    rest_api_name: str,
    description: str,
    stage_name: str,
    deploy: bool,
    endpoint_type: Literal["regional", "edge"],
) -> aws_apigateway.RestApi:
    """
    Represents an api gateway. Adds it to the passed stack.
    """

    endpoint_type_mapper = {
        "regional": aws_apigateway.EndpointType.REGIONAL,
        "edge": aws_apigateway.EndpointType.EDGE,
    }

    api = aws_apigateway.RestApi(
        stack,
        id,
        rest_api_name=rest_api_name,
        description=description,
        endpoint_types=[endpoint_type_mapper[endpoint_type]],
        deploy=deploy,
        deploy_options=aws_apigateway.StageOptions(stage_name=stage_name),
    )

    setattr(stack, id, api)

    return api


def add_existing_rest_api_gateway_to_stack(
    *, stack: Stack, id: str, rest_api_id: str, root_resource_id: str
) -> aws_apigateway.IRestApi:
    api = aws_apigateway.RestApi.from_rest_api_attributes(
        stack, id, rest_api_id=rest_api_id, root_resource_id=root_resource_id
    )

    setattr(stack, id, api)

    return api


def add_dynamodb_to_stack(
    *,
    stack: Stack,
    id: str,
    partition_key: DynamoDBKeyT,
    sort_key: DynamoDBKeyT,
    stream: DynamoDBStreamT,
    billing_mode: DynamoDBBillingModeT,
    remove_on_delete: bool,
    local_secondary_indexes: list[DynamoDBLsiT],
    global_secondary_indexes: list[DynamoDBGsiT],
):
    stream_mapper: dict[DynamoDBStreamT, aws_dynamodb.StreamViewType] = {
        "new_and_old_images": aws_dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        "new_image": aws_dynamodb.StreamViewType.NEW_IMAGE,
        "old_image": aws_dynamodb.StreamViewType.OLD_IMAGE,
    }

    billing_mode_mapper: dict[DynamoDBBillingModeT, aws_dynamodb.BillingMode] = {
        "pay_per_request": aws_dynamodb.BillingMode.PAY_PER_REQUEST,
    }

    attribute_type_mapper: dict[DynamoDBAttributeTypeT, aws_dynamodb.AttributeType] = {
        "string": aws_dynamodb.AttributeType.STRING,
        "number": aws_dynamodb.AttributeType.NUMBER,
        "binary": aws_dynamodb.AttributeType.BINARY,
    }

    removal_policy = RemovalPolicy.DESTROY if remove_on_delete else RemovalPolicy.RETAIN

    db = aws_dynamodb.Table(
        stack,
        id,
        partition_key=aws_dynamodb.Attribute(
            name=partition_key["key_name"],
            type=attribute_type_mapper[partition_key["key_type"]],
        ),
        sort_key=aws_dynamodb.Attribute(
            name=sort_key["key_name"],
            type=attribute_type_mapper[sort_key["key_type"]],
        ),
        billing_mode=billing_mode_mapper[billing_mode],
        stream=stream_mapper[stream],
        removal_policy=removal_policy,
    )

    for lsi in local_secondary_indexes:
        db.add_local_secondary_index(
            sort_key=aws_dynamodb.Attribute(
                name=lsi["sort_key"]["key_name"],
                type=attribute_type_mapper[lsi["sort_key"]["key_type"]],
            ),
            index_name=lsi["index_name"],
        )

    for gsi in global_secondary_indexes:
        db.add_global_secondary_index(
            partition_key=aws_dynamodb.Attribute(
                name=gsi["partition_key"]["key_name"],
                type=attribute_type_mapper[gsi["partition_key"]["key_type"]],
            ),
            sort_key=aws_dynamodb.Attribute(
                name=gsi["sort_key"]["key_name"],
                type=attribute_type_mapper[gsi["sort_key"]["key_type"]],
            ),
            index_name=gsi["index_name"],
        )

    setattr(stack, id, db)

    return db


def add_sns_topic_to_stack(
    *, stack: Stack, id: str, display_name: str
) -> aws_sns.Topic:
    sns = aws_sns.Topic(
        stack,
        id,
        display_name=display_name,
    )

    setattr(stack, id, sns)

    return sns


def add_s3_bucket_to_stack(
    *, stack: Stack, id: str, bucket_name: str, remove_on_delete: bool
) -> aws_s3.Bucket:
    bucket = aws_s3.Bucket(
        stack,
        id,
        bucket_name=bucket_name,
        removal_policy=(
            RemovalPolicy.DESTROY if remove_on_delete else RemovalPolicy.RETAIN
        ),
        auto_delete_objects=remove_on_delete,
    )

    setattr(stack, id, bucket)

    return bucket


def add_sqs_queue_to_stack(
    *, stack: Stack, id: str, queue_name: str, visibility_timeout: int
) -> aws_sqs.Queue:
    queue = aws_sqs.Queue(
        stack,
        id,
        queue_name=queue_name,
        visibility_timeout=Duration.seconds(visibility_timeout),
    )

    setattr(stack, id, queue)

    return queue
