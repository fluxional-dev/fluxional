from typing import Literal, Optional, TypeGuard
from dataclasses import dataclass, field
from .types import (
    ServerlessResourcesT,
    DynamoDBKeyT,
    DynamoDBStreamT,
    DynamoDBBillingModeT,
    DynamoDBLsiT,
    RateDurationUnitT,
    DynamoDBGsiT,
)


@dataclass(kw_only=True)
class _CorePermission:
    resource_id: str
    resource_type: ServerlessResourcesT


@dataclass(kw_only=True)
class LambdaPermission(_CorePermission):
    allow_invoke: bool = field(default=False)
    permission_type: Literal["lambda_permission"] = field(default="lambda_permission")


@dataclass(kw_only=True)
class BaseDbPermission(_CorePermission):
    allow_read: bool
    allow_write: bool


@dataclass(kw_only=True)
class DynamoDbPermission(BaseDbPermission):
    permission_type: Literal["dynamodb_permission"] = field(
        default="dynamodb_permission"
    )


@dataclass(kw_only=True)
class SnsPermission(_CorePermission):
    allow_publish: bool
    permission_type: Literal["sns_permission"] = field(default="sns_permission")


@dataclass(kw_only=True)
class WebsocketPermission(_CorePermission):
    allow_publish: bool
    permission_type: Literal["websocket_permission"] = field(
        default="websocket_permission"
    )


@dataclass(kw_only=True)
class S3Permission(_CorePermission):
    allow_read: bool
    allow_write: bool
    allow_delete: bool
    permission_type: Literal["s3_permission"] = field(default="s3_permission")


@dataclass(kw_only=True)
class SqsPermission(_CorePermission):
    allow_publish: bool
    permission_type: Literal["sqs_permission"] = field(default="sqs_permission")


AllPermission = (
    LambdaPermission
    | DynamoDbPermission
    | SnsPermission
    | WebsocketPermission
    | S3Permission
    | SqsPermission
)


@dataclass(kw_only=True)
class _ResourceT:
    id: str
    # resource type
    resource_type: ServerlessResourcesT
    # Permissions are InfrastructureModels inject at build time
    permissions: list[AllPermission] = field(default_factory=list)
    # Resource exist
    existing_resource: bool = field(default=False)


@dataclass(kw_only=True)
class LambdaFunction(_ResourceT):
    function_name: str
    directory: str = field(default="./")
    dockerfile: str = field(default="Dockerfile")
    memory_size: int = field(default=128)
    timeout: int = field(default=30)
    description: str = field(default="")
    resource_type: Literal["lambda_function"] = field(default="lambda_function")


@dataclass(kw_only=True)
class ApiGateway(_ResourceT):
    rest_api_name: str
    description: str = field(default="fluxional_api_gateway")
    endpoint_type: Literal["regional", "edge"] = field(default="regional")
    deploy: bool = field(default=True)
    stage_name: str = field(default="prod")
    allowed_methods: list[str] = field(default_factory=list)
    allowed_origins: list[str] = field(default_factory=list)
    allowed_credentials: bool = field(default=False)
    allowed_headers: list[str] = field(default_factory=list)
    # Existing Resource
    rest_api_id: Optional[str] = field(default=None)
    root_resource_id: Optional[str] = field(default=None)
    resource_type: Literal["api_gateway"] = field(default="api_gateway")


@dataclass(kw_only=True)
class WsGateway(_ResourceT):
    websocket_name: str
    stage_name: str = field(default="prod")
    auto_deploy: bool = field(default=True)
    routes: list[str] = field(default_factory=list)
    resource_type: Literal["ws_gateway"] = field(default="ws_gateway")


@dataclass(kw_only=True)
class DynamoDB(_ResourceT):
    partition_key: DynamoDBKeyT
    sort_key: DynamoDBKeyT
    resource_type: Literal["dynamodb"] = field(default="dynamodb")
    stream: DynamoDBStreamT = field(default="new_image")
    billing_mode: DynamoDBBillingModeT = field(default="pay_per_request")
    remove_on_delete: bool = field(default=True)
    local_secondary_indexes: list[DynamoDBLsiT] = field(default_factory=list)
    global_secondary_indexes: list[DynamoDBGsiT] = field(default_factory=list)


@dataclass(kw_only=True)
class SnsTopic(_ResourceT):
    display_name: str
    resource_type: Literal["sns_topic"] = field(default="sns_topic")


@dataclass(kw_only=True)
class SqsQueue(_ResourceT):
    queue_name: str
    visibility_timeout: int = field(default=30)
    resource_type: Literal["sqs_queue"] = field(default="sqs_queue")


@dataclass(kw_only=True)
class S3Bucket(_ResourceT):
    bucket_name: str
    remove_on_delete: bool = field(default=True)
    resource_type: Literal["s3_bucket"] = field(default="s3_bucket")


@dataclass(kw_only=True)
class RateSchedule(_ResourceT):
    schedule_name: str
    value: int | float
    unit: RateDurationUnitT
    resource_type: Literal["rate_schedule"] = field(default="rate_schedule")


@dataclass(kw_only=True)
class CronSchedule(_ResourceT):
    schedule_name: str
    day: str | None = field(default=None)
    hour: str | None = field(default=None)
    minute: str | None = field(default=None)
    month: str | None = field(default=None)
    week_day: str | None = field(default=None)
    year: str | None = field(default=None)
    resource_type: Literal["cron_schedule"] = field(default="cron_schedule")


AllResources = (
    LambdaFunction
    | ApiGateway
    | DynamoDB
    | SnsTopic
    | WsGateway
    | S3Bucket
    | RateSchedule
    | CronSchedule
    | SqsQueue
)


@dataclass(kw_only=True)
class InfraSettings:
    stack_name: str
    aws_account_id: Optional[str]
    aws_region: Optional[str]
    environment: dict[str, str] = field(default_factory=dict)


InfraResources = dict[str, AllResources]


@dataclass(kw_only=True)
class InfrastructureT:
    settings: InfraSettings
    resources: InfraResources


class ResourceTypeGuard:
    @staticmethod
    def is_lambda_permission(val: AllPermission) -> TypeGuard[LambdaPermission]:
        return val.permission_type == "lambda_permission"

    @staticmethod
    def is_dynamodb_permission(val: AllPermission) -> TypeGuard[DynamoDbPermission]:
        return val.permission_type == "dynamodb_permission"

    @staticmethod
    def is_sns_permission(val: AllPermission) -> TypeGuard[SnsPermission]:
        return val.permission_type == "sns_permission"

    @staticmethod
    def is_websocket_permission(val: AllPermission) -> TypeGuard[WebsocketPermission]:
        return val.permission_type == "websocket_permission"

    @staticmethod
    def is_s3_permission(val: AllPermission) -> TypeGuard[S3Permission]:
        return val.permission_type == "s3_permission"

    @staticmethod
    def is_sqs_permission(val: AllPermission) -> TypeGuard[SqsPermission]:
        return val.permission_type == "sqs_permission"


def parse_dict_to_resources(resources: dict[str, dict]) -> dict[str, AllResources]:
    parsed_resources: dict[str, AllResources] = {}

    for k in resources:
        # Parse the permissions
        permissions = resources[k].get("permissions")
        parsed_permissions: list[AllPermission] = []
        if permissions:
            for perm in permissions:
                if perm["resource_type"] == "lambda_function":
                    parsed_permissions.append(LambdaPermission(**perm))
                if perm["resource_type"] == "dynamodb":
                    parsed_permissions.append(DynamoDbPermission(**perm))
                if perm["resource_type"] == "sns_topic":
                    parsed_permissions.append(SnsPermission(**perm))
                if perm["resource_type"] == "ws_gateway":
                    parsed_permissions.append(WebsocketPermission(**perm))
                if perm["resource_type"] == "s3_bucket":
                    parsed_permissions.append(S3Permission(**perm))
                if perm["resource_type"] == "sqs_queue":
                    parsed_permissions.append(SqsPermission(**perm))

        resources[k].pop("permissions", None)
        # Parse the resource
        if resources[k]["resource_type"] == "lambda_function":
            parsed_resources[k] = LambdaFunction(
                permissions=parsed_permissions, **resources[k]
            )
        elif resources[k]["resource_type"] == "api_gateway":
            parsed_resources[k] = ApiGateway(
                permissions=parsed_permissions, **resources[k]
            )

        elif resources[k]["resource_type"] == "ws_gateway":
            parsed_resources[k] = WsGateway(
                permissions=parsed_permissions, **resources[k]
            )

        elif resources[k]["resource_type"] == "dynamodb":
            parsed_resources[k] = DynamoDB(
                permissions=parsed_permissions, **resources[k]
            )

        elif resources[k]["resource_type"] == "sns_topic":
            parsed_resources[k] = SnsTopic(
                permissions=parsed_permissions, **resources[k]
            )

        elif resources[k]["resource_type"] == "sqs_queue":
            parsed_resources[k] = SqsQueue(
                permissions=parsed_permissions, **resources[k]
            )

        elif resources[k]["resource_type"] == "s3_bucket":
            parsed_resources[k] = S3Bucket(
                permissions=parsed_permissions, **resources[k]
            )

        elif resources[k]["resource_type"] == "rate_schedule":
            parsed_resources[k] = RateSchedule(
                permissions=parsed_permissions, **resources[k]
            )

        elif resources[k]["resource_type"] == "cron_schedule":
            parsed_resources[k] = CronSchedule(
                permissions=parsed_permissions, **resources[k]
            )

    return parsed_resources
