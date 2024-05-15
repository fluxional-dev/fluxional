from fluxional.core.infrastructure.base import Infrastructure, MissingStackResource
import pytest
from aws_cdk.assertions import Template
from fluxional.core.tools import LookupKey


def test_sqs_queue():
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "sqs_queue_id": {
                "id": "sqs_queue_id",
                "resource_type": "sqs_queue",
                "queue_name": "test_queue",
                "permissions": [
                    {
                        "resource_id": "lambda_function_id",
                        "resource_type": "lambda_function",
                        "allow_invoke": True,
                    }
                ],
            },
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
            },
            "lambda_publisher_id": {
                "id": "lambda_publisher_id",
                "resource_type": "lambda_function",
                "function_name": "test_publisher",
                "dockerfile": "/tests/core/Dockerfile.lambda",
                "permissions": [
                    {
                        "resource_id": "sqs_queue_id",
                        "resource_type": "sqs_queue",
                        "allow_publish": True,
                    }
                ],
            },
        },
    }

    builder = Infrastructure.from_dict(infra)

    stack = builder.stack()

    template = Template.from_stack(stack)

    template.has_resource(
        "AWS::SQS::Queue",
        {"Properties": {"QueueName": "test_queue", "VisibilityTimeout": 30}},
    )

    template.has_resource(
        "AWS::IAM::Policy",
        {
            "Properties": {
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": [
                                "sqs:SendMessage",
                                "sqs:GetQueueAttributes",
                                "sqs:GetQueueUrl",
                            ],
                            "Effect": "Allow",
                            "Resource": {"Fn::GetAtt": ["sqsqueueidE428D9DD", "Arn"]},
                        }
                    ],
                    "Version": "2012-10-17",
                },
            }
        },
    )

    template.has_resource(
        "AWS::IAM::Policy",
        {
            "Properties": {
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": [
                                "sqs:ReceiveMessage",
                                "sqs:ChangeMessageVisibility",
                                "sqs:GetQueueUrl",
                                "sqs:DeleteMessage",
                                "sqs:GetQueueAttributes",
                            ],
                            "Effect": "Allow",
                            "Resource": {"Fn::GetAtt": ["sqsqueueidE428D9DD", "Arn"]},
                        }
                    ],
                    "Version": "2012-10-17",
                },
            }
        },
    )

    template.has_resource(
        "AWS::Lambda::Function",
        {
            "Properties": {
                "Environment": {
                    "Variables": {
                        "fluxional_resource_id": "lambda_publisher_id",
                        "fluxional_execution_context": "cloud",
                        "sqs_queue_id_queue_url": {},
                    }
                },
            }
        },
    )


def test_cron_schedule():
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "cron_schedule_id": {
                "id": "cron_schedule_id",
                "resource_type": "cron_schedule",
                "schedule_name": "TestSchedule",
                "day": "1",
                "hour": "2",
                "minute": "3",
                "month": "4",
                "week_day": None,
                "year": "2022",
                "permissions": [
                    {
                        "resource_id": "lambda_function_id",
                        "resource_type": "lambda_function",
                        "allow_invoke": True,
                    }
                ],
            },
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
            },
        },
    }

    builder = Infrastructure.from_dict(infra)

    stack = builder.stack()

    template = Template.from_stack(stack)

    template.has_resource(
        "AWS::Events::Rule",
        {
            "Properties": {
                "ScheduleExpression": "cron(3 2 1 4 ? 2022)",
                "Targets": [
                    {
                        "Input": '{"schedule_type":"CronSchedule","schedule_name":"TestSchedule"}',
                    }
                ],
            }
        },
    )

    template.has_resource(
        "AWS::Lambda::Permission", {"Properties": {"Action": "lambda:InvokeFunction"}}
    )


def test_rate_schedule():
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "rate_schedule_id": {
                "id": "rate_schedule_id",
                "resource_type": "rate_schedule",
                "schedule_name": "TestSchedule",
                "value": 1,
                "unit": "minutes",
                "permissions": [
                    {
                        "resource_id": "lambda_function_id",
                        "resource_type": "lambda_function",
                        "allow_invoke": True,
                    }
                ],
            },
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
            },
        },
    }

    builder = Infrastructure.from_dict(infra)

    stack = builder.stack()

    template = Template.from_stack(stack)

    template.has_resource(
        "AWS::Events::Rule",
        {
            "Properties": {
                "ScheduleExpression": "rate(1 minute)",
                "Targets": [
                    {
                        "Input": '{"schedule_type":"RateSchedule","schedule_name":"TestSchedule"}',
                    }
                ],
            }
        },
    )

    template.has_resource(
        "AWS::Lambda::Permission", {"Properties": {"Action": "lambda:InvokeFunction"}}
    )


def test_infrastructure_build_stack():
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "api_gateway_id": {
                "id": "api_gateway_id",
                "resource_type": "api_gateway",
                "rest_api_name": "123456",
                "permissions": [
                    {
                        "resource_id": "lambda_function_id",
                        "resource_type": "lambda_function",
                        "allow_invoke": True,
                    }
                ],
            },
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
            },
        },
    }

    builder = Infrastructure.from_dict(infra)

    stack = builder.stack()

    assert stack.app

    builder.resources.pop("lambda_function_id", None)

    with pytest.raises(MissingStackResource):
        builder.stack()


def test_infrastructure_add_lambda_function():
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
            "environment": {"TEST": "test", LookupKey.handler_context: "development"},
        },
        "resources": {
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
            },
        },
    }

    builder = Infrastructure.from_dict(infra)

    stack = builder.stack()

    template = Template.from_stack(stack)

    template.has_resource(
        "AWS::Lambda::Function",
        {
            "Properties": {
                "MemorySize": 128,
                "Timeout": 30,
                "Environment": {
                    "Variables": {
                        "TEST": "test",
                        LookupKey.resource_id: "lambda_function_id",
                        LookupKey.execution_context: "cloud",
                    }
                },
            }
        },
    )

    # There should be an iam policy to trigger iot because fluxional_handler_context is development
    template.has_resource(
        "AWS::IAM::Policy",
        {
            "Properties": {
                "PolicyDocument": {
                    "Statement": [
                        {"Action": "iot:Connect", "Effect": "Allow", "Resource": "*"},
                        {
                            "Action": ["iot:Publish", "iot:Receive"],
                            "Effect": "Allow",
                            "Resource": "arn:aws:iot:*:*:topic/fluxional*",
                        },
                        {
                            "Action": "iot:Subscribe",
                            "Effect": "Allow",
                            "Resource": "arn:aws:iot:*:*:topicfilter/fluxional*",
                        },
                        {
                            "Action": "iot:DescribeEndpoint",
                            "Effect": "Allow",
                            "Resource": "*",
                        },
                    ]
                }
            }
        },
    )


def test_infrastructure_add_dynamodb():
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            # Adding lambda to check that it will add the permission
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
                "permissions": [
                    {
                        "resource_id": "dynamodb_id",
                        "resource_type": "dynamodb",
                        "allow_read": True,
                        "allow_write": True,
                    }
                ],
            },
            "dynamodb_id": {
                "id": "dynamodb_id",
                "resource_type": "dynamodb",
                "partition_key": {"key_name": "pk", "key_type": "string"},
                "sort_key": {"key_name": "sk", "key_type": "string"},
                "local_secondary_indexes": [
                    {
                        "index_name": "some_index_name",
                        "sort_key": {"key_name": "some_key_name", "key_type": "string"},
                    }
                ],
            },
        },
    }

    builder = Infrastructure.from_dict(infra)

    stack = builder.stack()

    template = Template.from_stack(stack)

    template.has_resource(
        "AWS::DynamoDB::Table",
        {
            "Properties": {
                "LocalSecondaryIndexes": [
                    {
                        "IndexName": "some_index_name",
                    }
                ]
            }
        },
    )

    # Test that table name is injected in secrets
    # Test that the environment for secret arn is injected
    resources = template.to_json()["Resources"]

    data = [
        resources[k]
        for k, v in resources.items()
        if v["Type"] == "AWS::Lambda::Function"
    ][0]["Properties"]["Environment"]["Variables"]

    assert "dynamodb_id_table_name" in data


def test_infrastructure_add_rest_api_gateway():
    # New Api Gateway
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "api_gateway_id": {
                "id": "api_gateway_id",
                "resource_type": "api_gateway",
                "rest_api_name": "123456",
                "permissions": [
                    {
                        "resource_id": "lambda_function_id",
                        "resource_type": "lambda_function",
                        "allow_invoke": True,
                    }
                ],
            },
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
            },
        },
    }

    builder = Infrastructure.from_dict(infra)
    stack = builder.stack()
    template = Template.from_stack(stack)
    template.has_resource("AWS::ApiGateway::RestApi", {})
    template.has_resource("AWS::Lambda::Permission", {})
    template.has_resource(
        "AWS::Lambda::Function",
        {
            "Properties": {
                "Environment": {
                    "Variables": {
                        # Stage name is injected
                        LookupKey.api_path_prefix: "/prod",
                    }
                },
            }
        },
    )

    # Existing Api Gateway
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "api_gateway_id": {
                "id": "api_gateway_id",
                "rest_api_name": "123456",
                "resource_type": "api_gateway",
                "rest_api_id": "some_rest_api_id",
                "root_resource_id": "some_root_resource_id",
                "existing_resource": True,
                "permissions": [
                    {
                        "resource_id": "lambda_function_id",
                        "resource_type": "lambda_function",
                        "allow_invoke": True,
                    }
                ],
            },
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
            },
        },
    }

    builder = Infrastructure.from_dict(infra)
    stack = builder.stack()
    template = Template.from_stack(stack)
    template.has_resource("AWS::ApiGateway::Resource", {})
    template.has_resource("AWS::Lambda::Permission", {})


def test_infrastructure_add_sns_topic():
    # New SNS Topic
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "sns_topic_id": {
                "id": "sns_topic_id",
                "resource_type": "sns_topic",
                "display_name": "test_topic",
            },
        },
    }

    builder = Infrastructure.from_dict(infra)
    stack = builder.stack()
    template = Template.from_stack(stack)
    template.has_resource("AWS::SNS::Topic", {})

    # Add a lambda and subscription to the topic
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "sns_topic_id": {
                "id": "sns_topic_id",
                "resource_type": "sns_topic",
                "display_name": "test_topic",
                "permissions": [
                    {
                        "resource_id": "lambda_function_id",
                        "resource_type": "lambda_function",
                        "allow_invoke": True,
                    }
                ],
            },
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
            },
            "lambda_publisher_id": {
                "id": "lambda_publisher_id",
                "resource_type": "lambda_function",
                "function_name": "test_publisher",
                "dockerfile": "/tests/core/Dockerfile.lambda",
                "permissions": [
                    {
                        "resource_id": "sns_topic_id",
                        "resource_type": "sns_topic",
                        "allow_publish": True,
                    }
                ],
            },
        },
    }

    builder = Infrastructure.from_dict(infra)
    stack = builder.stack()
    template = Template.from_stack(stack)
    template.has_resource("AWS::SNS::Topic", {})
    template.has_resource("AWS::Lambda::Permission", {})
    template.has_resource("AWS::SNS::Subscription", {})
    # Check that lambda has the environment variable topic arn injected
    template.has_resource(
        "AWS::Lambda::Function",
        {
            "Properties": {
                "Environment": {"Variables": {"sns_topic_id_topic_arn": {}}},
            }
        },
    )


def test_from_dict():
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
            },
            "api_gateway_id": {
                "id": "api_gateway_id",
                "resource_type": "api_gateway",
                "rest_api_name": "123456",
                "permissions": [
                    {
                        "resource_id": "lambda_function_id",
                        "resource_type": "lambda_function",
                        "allow_invoke": True,
                    }
                ],
            },
        },
    }

    builder = Infrastructure.from_dict(infra)

    assert builder.settings.aws_account_id == "123456789"
    assert builder.settings.aws_region == "us-east-1"
    assert builder.settings.stack_name == "TestStack"
    assert builder.resources["lambda_function_id"].resource_type == "lambda_function"
    assert builder.resources["api_gateway_id"].resource_type == "api_gateway"


def test_ws_gateway():
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "ws_gateway_id": {
                "id": "ws_gateway_id",
                "websocket_name": "test_ws",
                "resource_type": "ws_gateway",
                "stage_name": "prod",
                "auto_deploy": True,
                "routes": ["$connect", "$disconnect", "$default"],
                "permissions": [
                    {
                        "resource_id": "lambda_function_id",
                        "resource_type": "lambda_function",
                        "allow_invoke": True,
                    }
                ],
            },
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
            },
            "some_other_lambda_function_id": {
                "id": "some_other_lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
                "permissions": [
                    {
                        "resource_id": "ws_gateway_id",
                        "resource_type": "ws_gateway",
                        "allow_publish": True,
                    }
                ],
            },
        },
    }

    builder = Infrastructure.from_dict(infra)

    stack = builder.stack()

    template = Template.from_stack(stack)

    template.has_resource("AWS::Lambda::Function", {})
    template.has_resource("AWS::Lambda::Permission", {})
    template.has_resource("AWS::ApiGatewayV2::Api", {})
    template.has_resource(
        "AWS::ApiGatewayV2::Stage",
        {"Properties": {"AutoDeploy": True, "StageName": "prod"}},
    )
    template.has_resource(
        "AWS::ApiGatewayV2::Route", {"Properties": {"RouteKey": "$default"}}
    )
    template.has_resource(
        "AWS::ApiGatewayV2::Route", {"Properties": {"RouteKey": "$connect"}}
    )
    template.has_resource(
        "AWS::ApiGatewayV2::Route", {"Properties": {"RouteKey": "$disconnect"}}
    )

    # Make sure env variable is injected in the lambda that can publish to websocket
    template.has_resource(
        "AWS::Lambda::Function",
        {
            "Properties": {
                "Environment": {
                    "Variables": {
                        "ws_gateway_id_api_id": {},
                        "ws_gateway_id_stage_name": "prod",
                    }
                }
            }
        },
    )


def test_ws_gw_raise_error_with_more_perm():
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "ws_gateway_id": {
                "id": "ws_gateway_id",
                "resource_type": "ws_gateway",
                "websocket_name": "test_ws",
                "stage_name": "prod",
                "auto_deploy": True,
                "routes": ["$connect", "$disconnect", "$default"],
                "permissions": [
                    {
                        "resource_id": "lambda_function_id",
                        "resource_type": "lambda_function",
                        "allow_invoke": True,
                    },
                    {
                        "resource_id": "lambda_function_id",
                        "resource_type": "lambda_function",
                        "allow_invoke": True,
                    },
                ],
            },
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
            },
        },
    }

    with pytest.raises(ValueError):
        builder = Infrastructure.from_dict(infra)
        builder.stack()


def test_add_s3_bucket():
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "s3_bucket_id": {
                "id": "s3_bucket_id",
                "resource_type": "s3_bucket",
                "bucket_name": "testbucket",
                "remove_on_delete": True,
            },
        },
    }

    builder = Infrastructure.from_dict(infra)
    stack = builder.stack()
    template = Template.from_stack(stack)
    template.has_resource(
        "AWS::S3::Bucket",
        {"Properties": {"BucketName": "testbucket"}, "DeletionPolicy": "Delete"},
    )


def test_dependency_error():
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "s3_bucket_id": {
                "id": "s3_bucket_id",
                "resource_type": "s3_bucket",
                "bucket_name": "testbucket",
                "remove_on_delete": True,
                "permissions": [
                    {
                        "resource_id": "lambda_function_id",
                        "resource_type": "lambda_function",
                        "allow_invoke": True,
                    }
                ],
            },
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
                "permissions": [
                    {
                        "resource_id": "s3_bucket_id",
                        "resource_type": "s3_bucket",
                        "allow_read": True,
                        "allow_write": True,
                        "allow_delete": True,
                    }
                ],
            },
        },
    }

    with pytest.raises(ValueError):
        builder = Infrastructure.from_dict(infra)
        builder.stack()


def test_add_s3_bucket_with_lambda_invoke_permission():
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "s3_bucket_id": {
                "id": "s3_bucket_id",
                "resource_type": "s3_bucket",
                "bucket_name": "testbucket",
                "remove_on_delete": True,
                "permissions": [
                    {
                        "resource_id": "lambda_function_id",
                        "resource_type": "lambda_function",
                        "allow_invoke": True,
                    }
                ],
            },
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
                "permissions": [],
            },
        },
    }

    builder = Infrastructure.from_dict(infra)
    stack = builder.stack()
    template = Template.from_stack(stack)

    template.has_resource(
        "AWS::Lambda::Permission",
        {
            "Properties": {
                "Action": "lambda:InvokeFunction",
                "Principal": "s3.amazonaws.com",
            },
        },
    )
    template.has_resource_properties(
        "Custom::S3BucketNotifications",
        {
            "NotificationConfiguration": {
                "LambdaFunctionConfigurations": [
                    {
                        "Events": ["s3:ObjectCreated:*"],
                    },
                    {
                        "Events": ["s3:ObjectRemoved:*"],
                    },
                ]
            },
        },
    )

    template.has_resource(
        "AWS::IAM::Policy",
        {
            "Properties": {
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": ["s3:GetObject*", "s3:GetBucket*", "s3:List*"],
                            "Effect": "Allow",
                        },
                    ],
                },
            },
        },
    )


def test_add_s3_bucket_with_lambda_read_write_delete_permission():
    infra = {
        "settings": {
            "aws_account_id": "123456789",
            "aws_region": "us-east-1",
            "stack_name": "TestStack",
        },
        "resources": {
            "s3_bucket_id": {
                "id": "s3_bucket_id",
                "resource_type": "s3_bucket",
                "bucket_name": "testbucket",
                "remove_on_delete": True,
                "permissions": [],
            },
            "lambda_function_id": {
                "id": "lambda_function_id",
                "resource_type": "lambda_function",
                "function_name": "test_function",
                "dockerfile": "/tests/core/Dockerfile.lambda",
                "permissions": [
                    {
                        "resource_id": "s3_bucket_id",
                        "resource_type": "s3_bucket",
                        "allow_read": True,
                        "allow_write": True,
                        "allow_delete": True,
                    }
                ],
            },
        },
    }

    builder = Infrastructure.from_dict(infra)
    stack = builder.stack()
    template = Template.from_stack(stack)

    template.has_resource(
        "AWS::IAM::Policy",
        {
            "Properties": {
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": ["s3:GetObject*", "s3:GetBucket*", "s3:List*"],
                            "Effect": "Allow",
                        },
                        {
                            "Action": [
                                "s3:DeleteObject*",
                                "s3:PutObject",
                                "s3:PutObjectLegalHold",
                                "s3:PutObjectRetention",
                                "s3:PutObjectTagging",
                                "s3:PutObjectVersionTagging",
                                "s3:Abort*",
                            ],
                            "Effect": "Allow",
                        },
                        {
                            "Action": "s3:DeleteObject*",
                            "Effect": "Allow",
                        },
                    ],
                },
            },
        },
    )

    # Lambda should have bucket name
    template.has_resource(
        "AWS::Lambda::Function",
        {
            "Properties": {
                "Environment": {
                    "Variables": {
                        "s3_bucket_id_bucket_name": {},
                    }
                }
            }
        },
    )
