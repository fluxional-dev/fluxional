from typing import TypedDict, Literal

# RESOURCES
ServerlessResourcesT = Literal[
    "lambda_function",
    "api_gateway",
    "ws_gateway",
    "dynamodb",
    "sns_topic",
    "s3_bucket",
    "rate_schedule",
    "cron_schedule",
    "sqs_queue",
]

# DYNAMODB
DynamoDBBillingModeT = Literal["pay_per_request"]
DynamoDBStreamT = Literal["new_image", "old_image", "new_and_old_images"]
DynamoDBAttributeTypeT = Literal["string", "number", "binary"]
RateDurationUnitT = Literal["days", "hours", "minutes", "seconds", "milliseconds"]


class DynamoDBKeyT(TypedDict):
    key_name: str
    key_type: DynamoDBAttributeTypeT


class DynamoDBLsiT(TypedDict):
    index_name: str
    sort_key: DynamoDBKeyT


class DynamoDBGsiT(TypedDict):
    index_name: str
    partition_key: DynamoDBKeyT
    sort_key: DynamoDBKeyT
