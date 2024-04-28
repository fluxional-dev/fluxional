import boto3  # type: ignore
import json
from typing import TypeVar, Generic, Optional
from .types import WsEvent
import os
from dataclasses import dataclass, field


@dataclass
class LookupKey:
    handler_context: str = "fluxional_handler_context"
    execution_context: str = "fluxional_execution_context"
    dynamodb_table_name: str = "fluxional_dynamodb_table_name"
    storage_bucket_name: str = "fluxional_storage_bucket_bucket_name"
    api_path_prefix: str = "fluxional_api_path_prefix"
    resource_id: str = "fluxional_resource_id"
    websocket_api_id: str = "fluxional_websocket_gateway_api_id"
    websocket_stage_name: str = "fluxional_websocket_gateway_stage_name"
    event_queue_url: str = "fluxional_event_queue_queue_url"


@dataclass
class Environment:
    # execution_context
    execution_context: Optional[str] = field(
        default_factory=lambda: os.environ.get(LookupKey.execution_context)
    )

    # fluxional_run_context
    fluxional_handler_context: Optional[str] = field(
        default_factory=lambda: os.environ.get(LookupKey.handler_context)
    )

    # If a dynamodb is in the stack this will have the table name
    dynamodb_table_name: Optional[str] = field(
        default_factory=lambda: os.environ.get(LookupKey.dynamodb_table_name)
    )

    # If an storage bucket permission is in the stack this will have the bucket name
    storage_bucket_name: Optional[str] = field(
        default_factory=lambda: os.environ.get(LookupKey.storage_bucket_name)
    )

    # This will be the stage name of the API Gateway but with a slash in front. ex: /prod
    api_path_prefix: str = field(
        default_factory=lambda: os.environ.get(LookupKey.api_path_prefix) or ""
    )

    # resource_id
    resource_id: Optional[str] = field(
        default_factory=lambda: os.environ.get(LookupKey.resource_id)
    )

    # Web socket api id
    websocket_api_id: Optional[str] = field(
        default_factory=lambda: os.environ.get(LookupKey.websocket_api_id)
    )

    # Web socket stage name
    websocket_stage_name: Optional[str] = field(
        default_factory=lambda: os.environ.get(LookupKey.websocket_stage_name)
    )

    # Event sqs queue url
    event_queue_url: Optional[str] = field(
        default_factory=lambda: os.environ.get(LookupKey.event_queue_url)
    )

    # AWS Credentials
    aws_access_key_id: Optional[str] = field(
        default_factory=lambda: os.environ.get("AWS_ACCESS_KEY_ID")
    )
    aws_secret_access_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("AWS_SECRET_ACCESS_KEY")
    )
    aws_session_token: Optional[str] = field(
        default_factory=lambda: os.environ.get("AWS_SESSION_TOKEN")
    )
    aws_region: Optional[str] = field(
        default_factory=lambda: os.environ.get("AWS_DEFAULT_REGION")
        or os.environ.get("AWS_REGION")
    )


T = TypeVar("T")


class Event(Generic[T]):
    def __init__(self):
        self._env = Environment()
        self._sqs = boto3.client("sqs", region_name=self._env.aws_region)

    def trigger(self, event_name: str, data: T) -> None:
        self._sqs.send_message(
            QueueUrl=self._env.event_queue_url,
            MessageBody=json.dumps(
                {
                    "event_name": event_name,
                    "data": data,
                }
            ),
        )


class Websocket:
    @staticmethod
    def post_to_connection(
        event: WsEvent, data: str, *, connection_id: str | None = None
    ):
        """
        Respond to a WebSocket connection id with data. if no connection_id is provided, it will be extracted from the event.
        """
        if not connection_id:
            connection_id = event["requestContext"]["connectionId"]

        api_gateway_management = boto3.client(
            "apigatewaymanagementapi",
            endpoint_url=f"https://{event['requestContext']['domainName']}/{event['requestContext']['stage']}",
        )
        api_gateway_management.post_to_connection(Data=data, ConnectionId=connection_id)
