from fluxional.core.infrastructure.cdk import (
    add_lambda_function_to_stack,
    add_existing_rest_api_gateway_to_stack,
    add_rest_api_gateway_to_stack,
    add_dynamodb_to_stack,
    add_sns_topic_to_stack,
    add_ws_gateway_to_stack,
    add_s3_bucket_to_stack,
    add_rate_schedule_to_stack,
    add_cron_schedule_to_stack,
    add_sqs_queue_to_stack,
)
from aws_cdk import Stack, App
from aws_cdk.assertions import Template
import pytest


@pytest.fixture
def mock_stack():
    app = App()

    class MockStack(Stack):
        def __init__(self, id: str, app: App):
            super().__init__(app, id)

    return MockStack(
        "MockStack",
        app,
    )


def test_add_cron_schedule_to_stack(mock_stack):
    add_cron_schedule_to_stack(
        stack=mock_stack,
        id="some_id",
        schedule_name="some_schedule_name",
        day=None,
        hour="1",
        minute="1",
        month="1",
        week_day="1",
        year="1",
    )

    template = Template.from_stack(mock_stack)

    template.has_resource(
        "AWS::Events::Rule",
        {
            "Properties": {
                "ScheduleExpression": "cron(1 1 ? 1 1 1)",
            }
        },
    )


def test_add_minutes_rate_schedule_to_stack(mock_stack):
    # minutes
    add_rate_schedule_to_stack(
        stack=mock_stack, id="minutes", unit="minutes", value=1, schedule_name="minutes"
    )

    template = Template.from_stack(mock_stack)

    template.has_resource(
        "AWS::Events::Rule",
        {
            "Properties": {
                "ScheduleExpression": "rate(1 minute)",
            }
        },
    )


def test_add_hours_rate_schedule_to_stack(mock_stack):
    # hours
    add_rate_schedule_to_stack(
        stack=mock_stack, id="hours", unit="hours", value=1, schedule_name="hours"
    )

    template = Template.from_stack(mock_stack)

    template.has_resource(
        "AWS::Events::Rule",
        {
            "Properties": {
                "ScheduleExpression": "rate(1 hour)",
            }
        },
    )


def test_add_days_rate_schedule_to_stack(mock_stack):
    # days
    add_rate_schedule_to_stack(
        stack=mock_stack, id="days", unit="days", value=1, schedule_name="days"
    )

    template = Template.from_stack(mock_stack)

    template.has_resource(
        "AWS::Events::Rule",
        {
            "Properties": {
                "ScheduleExpression": "rate(1 day)",
            }
        },
    )


def test_add_dynamodb_to_stack(mock_stack):
    add_dynamodb_to_stack(
        stack=mock_stack,
        id="some_id",
        partition_key={"key_name": "pk", "key_type": "string"},
        sort_key={"key_name": "sk", "key_type": "string"},
        billing_mode="pay_per_request",
        stream="new_and_old_images",
        remove_on_delete=True,
        local_secondary_indexes=[
            {
                "index_name": "some_index_name",
                "sort_key": {"key_name": "some_key_name", "key_type": "string"},
            }
        ],
        global_secondary_indexes=[
            {
                "index_name": "some_global_index_name",
                "partition_key": {"key_name": "some_key_name", "key_type": "string"},
                "sort_key": {"key_name": "some_key_name", "key_type": "string"},
            }
        ],
    )

    template = Template.from_stack(mock_stack)
    template.has_resource(
        "AWS::DynamoDB::Table",
        {
            "Properties": {
                "LocalSecondaryIndexes": [
                    {
                        "IndexName": "some_index_name",
                    }
                ],
                "GlobalSecondaryIndexes": [
                    {
                        "IndexName": "some_global_index_name",
                    }
                ],
            }
        },
    )


def test_add_lambda_function_to_stack(mock_stack):
    add_lambda_function_to_stack(
        stack=mock_stack,
        id="some_id",
        description="description",
        function_name="function_name",
        memory_size=128,
        timeout=60,
        directory="./tests/core/",
        file="Dockerfile.lambda",
    )

    template = Template.from_stack(mock_stack)

    template.has_resource(
        "AWS::Lambda::Function", {"Properties": {"MemorySize": 128, "Timeout": 60}}
    )


def test_add_rest_api_gateway_to_stack(mock_stack):
    api_gw = add_rest_api_gateway_to_stack(
        stack=mock_stack,
        id="some_id",
        rest_api_name="some_name",
        description="some_description",
        stage_name="some_stage_name",
        deploy=True,
        endpoint_type="regional",
    )

    api_gw.root.add_proxy(
        any_method=True,
    )

    template = Template.from_stack(mock_stack)

    template.has_resource("AWS::ApiGateway::RestApi", {})


def test_add_existing_rest_api_gateway_to_stack(mock_stack):
    api_gw = add_existing_rest_api_gateway_to_stack(
        stack=mock_stack,
        id="some_id",
        rest_api_id="some_rest_api_id",
        root_resource_id="some_root_resource_id",
    )

    api_gw.root.add_proxy(
        any_method=True,
    )

    template = Template.from_stack(mock_stack)

    template.has_resource("AWS::ApiGateway::Resource", {})


def test_add_sns_topic_to_stack(mock_stack):
    add_sns_topic_to_stack(
        stack=mock_stack,
        id="some_id",
        display_name="some_display_name",
    )

    template = Template.from_stack(mock_stack)

    template.has_resource(
        "AWS::SNS::Topic", {"Properties": {"DisplayName": "some_display_name"}}
    )


def test_add_ws_gateway_to_stack(mock_stack):
    add_ws_gateway_to_stack(
        stack=mock_stack,
        id="some_id",
        stage_name="some_stage_name",
        auto_deploy=True,
        websocket_name="some_websocket_name",
    )

    template = Template.from_stack(mock_stack)

    template.has_resource(
        "AWS::ApiGatewayV2::Api", {"Properties": {"Name": "some_websocket_name"}}
    )


def test_add_s3_bucket_to_stack(mock_stack):
    add_s3_bucket_to_stack(
        stack=mock_stack,
        id="some_id",
        bucket_name="somebucketname",
        remove_on_delete=True,
    )

    template = Template.from_stack(mock_stack)

    template.has_resource(
        "AWS::S3::Bucket",
        {"Properties": {"BucketName": "somebucketname"}, "DeletionPolicy": "Delete"},
    )


def test_add_sqs_queue_to_stack(mock_stack):
    add_sqs_queue_to_stack(
        stack=mock_stack,
        id="some_id",
        queue_name="some_queue_name",
        visibility_timeout=30,
    )

    template = Template.from_stack(mock_stack)

    template.has_resource(
        "AWS::SQS::Queue",
        {"Properties": {"QueueName": "some_queue_name"}},
    )
