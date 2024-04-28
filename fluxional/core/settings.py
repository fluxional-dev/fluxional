from dataclasses import dataclass, field
from typing import Optional, Literal
from .infrastructure.types import DynamoDBKeyT, DynamoDBStreamT, DynamoDBBillingModeT
from fluxional.core.tools import LookupKey

_OTEL_ENVS = [
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_EXPORTER_OTLP_HEADERS",
    "OTEL_SERVICE_NAME",
    "AWS_LAMBDA_EXEC_WRAPPER",
]


def _default_dynamodb_pk() -> DynamoDBKeyT:
    return {"key_name": "pk", "key_type": "string"}


def _default_dynamodb_sk() -> DynamoDBKeyT:
    return {"key_name": "sk", "key_type": "string"}


def _default_build_environment() -> list[str]:
    return [LookupKey.handler_context] + _OTEL_ENVS


@dataclass
class SystemSettings:
    # IDs
    default_dynamodb_id: str = field(default="fluxional_dynamodb")
    default_websocket_lambda_id: str = field(default="fluxional_websocket_lambda")
    default_api_lambda_id: str = field(default="fluxional_api_lambda")
    default_api_gateway_id: str = field(default="fluxional_api_gateway")
    default_websocket_gateway_id: str = field(default="fluxional_websocket_gateway")
    default_storage_bucket_id: str = field(default="fluxional_storage_bucket")
    default_storage_lambda_id: str = field(default="fluxional_storage_lambda")
    default_rate_schedule_task_lambda_id: str = field(
        default="fluxional_rate_schedule_task_lambda"
    )
    default_cron_schedule_task_lambda_id: str = field(
        default="fluxional_cron_schedule_task_lambda"
    )
    default_event_lambda_id: str = field(default="fluxional_event_lambda")
    default_event_queue_id: str = field(default="fluxional_event_queue")
    # Build
    build_environment: list[str] = field(default_factory=_default_build_environment)
    # Lambda Handler Override
    lambda_handler: Optional[str] = field(default=None)
    # Container CMD Override
    container_command: Optional[str] = field(default=None)
    # OTel
    aws_lambda_exec_wrapper: str = field(default="/opt/otel-instrument")


@dataclass
class PermissionSettings:
    # Database
    allow_api_to_write_to_db: bool = field(default=False)
    allow_api_to_read_from_db: bool = field(default=False)
    allow_websockets_to_read_from_db: bool = field(default=False)
    allow_websockets_to_write_to_db: bool = field(default=False)
    allow_storage_to_write_to_db: bool = field(default=False)
    allow_storage_to_read_from_db: bool = field(default=False)
    allow_events_to_write_to_db: bool = field(default=False)
    allow_events_to_read_from_db: bool = field(default=False)
    allow_tasks_to_write_to_db: bool = field(default=False)
    allow_tasks_to_read_from_db: bool = field(default=False)
    # Storage
    allow_api_to_write_to_storage: bool = field(default=False)
    allow_api_to_read_from_storage: bool = field(default=False)
    allow_api_to_delete_from_storage: bool = field(default=False)
    allow_websockets_to_write_to_storage: bool = field(default=False)
    allow_websockets_to_read_from_storage: bool = field(default=False)
    allow_websockets_to_delete_from_storage: bool = field(default=False)
    allow_storage_to_write_to_storage: bool = field(default=False)
    allow_storage_to_read_from_storage: bool = field(default=False)
    allow_storage_to_delete_from_storage: bool = field(default=False)
    allow_events_to_write_to_storage: bool = field(default=False)
    allow_events_to_read_from_storage: bool = field(default=False)
    allow_events_to_delete_from_storage: bool = field(default=False)
    allow_tasks_to_write_to_storage: bool = field(default=False)
    allow_tasks_to_read_from_storage: bool = field(default=False)
    allow_tasks_to_delete_from_storage: bool = field(default=False)

    # Events
    allow_api_to_run_events: bool = field(default=False)
    allow_websockets_to_run_events: bool = field(default=False)
    allow_storage_to_run_events: bool = field(default=False)
    allow_events_to_run_events: bool = field(default=False)
    allow_tasks_to_run_events: bool = field(default=False)


@dataclass
class DynamoDBSettings:
    default_primary_key: DynamoDBKeyT = field(default_factory=_default_dynamodb_pk)
    default_secondary_key: DynamoDBKeyT = field(default_factory=_default_dynamodb_sk)
    default_remove_on_delete: bool = field(default=True)
    default_billing_mode: DynamoDBBillingModeT = field(default="pay_per_request")
    default_stream: DynamoDBStreamT = field(default="new_image")


@dataclass
class CredentialsSettings:
    aws_account_id: Optional[str] = field(default=None)
    aws_region: Optional[str] = field(default=None)
    aws_access_key_id: Optional[str] = field(default=None)
    aws_secret_access_key: Optional[str] = field(default=None)


@dataclass
class LambdaSettings:
    directory: str = field(default="./")
    dockerfile: str = field(default="Dockerfile")
    memory_size: Literal[128, 512, 1024, 1536] = field(default=128)
    timeout: int = field(default=30)
    description: str = field(default="")


@dataclass
class ApiGatewaySettings:
    stage_name: str = field(default="prod")
    deploy: bool = field(default=True)
    description: str = field(default="fluxional_api_gateway")
    endpoint_type: Literal["regional", "edge"] = field(default="regional")


@dataclass
class WebsocketSettings:
    stage_name: str = field(default="prod")
    auto_deploy: bool = field(default=True)


@dataclass
class BuildSettings:
    dependencies: list[str] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)
    requirements_file: Optional[str] = field(default="requirements.txt")
    build_path: Optional[str] = field(default=None)
    api_lambda: LambdaSettings = field(default_factory=LambdaSettings)
    storage_lambda: LambdaSettings = field(default_factory=LambdaSettings)
    event_lambda: LambdaSettings = field(default_factory=LambdaSettings)
    api_gateway: ApiGatewaySettings = field(default_factory=ApiGatewaySettings)
    websocket: WebsocketSettings = field(default_factory=WebsocketSettings)
    dynamodb: DynamoDBSettings = field(default_factory=DynamoDBSettings)
    scheduled_task_lambda: LambdaSettings = field(default_factory=LambdaSettings)


@dataclass
class OpenTelemetrySettings:
    enable: bool = field(default=False)
    exporter_otlp_endpoint: str = field(default="https://")
    exporter_otlp_headers: str = field(default="")
    service_name: str = field(default="")


@dataclass
class FluxionalTelemetrySettings:
    enable: bool = field(default=False)


@dataclass
class MonitoringSettings:
    otel: OpenTelemetrySettings = field(default_factory=OpenTelemetrySettings)
    telemetry: FluxionalTelemetrySettings = field(
        default_factory=FluxionalTelemetrySettings
    )


@dataclass
class DevelopmentSettings:
    enable_local: bool = field(default=False)


@dataclass
class StorageSettings:
    enable: bool = field(default=False)
    remove_on_delete: bool = field(default=True)


@dataclass
class Settings:
    stack_name: str = ""
    # Credentials
    credentials: CredentialsSettings = field(default_factory=CredentialsSettings)

    # Build
    build: BuildSettings = field(default_factory=BuildSettings)

    # Permissions
    permissions: PermissionSettings = field(default_factory=PermissionSettings)

    # System settings
    system: SystemSettings = field(default_factory=SystemSettings)

    # Dev
    development: DevelopmentSettings = field(default_factory=DevelopmentSettings)

    # Monitoring
    monitoring: MonitoringSettings = field(default_factory=MonitoringSettings)

    # Storage
    storage: StorageSettings = field(default_factory=StorageSettings)

    def configure(
        self,
        *,
        aws_account_id: str | None = None,
        aws_region: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        dependencies: list[str] = [],
        environment: dict[str, str] = {},
        requirements_file: str | None = "requirements.txt",
    ) -> None:
        self.credentials.aws_access_key_id = aws_access_key_id
        self.credentials.aws_secret_access_key = aws_secret_access_key
        self.credentials.aws_region = aws_region
        self.credentials.aws_account_id = aws_account_id
        self.build.dependencies = dependencies
        self.build.environment = environment
        self.build.requirements_file = requirements_file
