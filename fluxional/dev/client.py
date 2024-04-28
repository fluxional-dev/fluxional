from awscrt import auth  # type: ignore
from awsiot import mqtt_connection_builder, mqtt  # type: ignore
import boto3  # type: ignore
from uuid import uuid4
from typing import Callable
import json


class AWSIotConnection:
    def __init__(
        self,
        *,
        endpoint: str | None = None,
        client_id: str | None = None,
        region: str | None = "us-east-1",
        clean_session: bool = False,
        keep_alive_secs: int = 30,
    ):
        self._endpoint = endpoint or self.default_iot_endpoint()
        self._client_id = client_id or self.default_client_id()
        self._region = region
        self._clean_session = clean_session
        self._keep_alive_secs = keep_alive_secs

    def credentials_provider(self) -> auth.AwsCredentialsProvider:
        return auth.AwsCredentialsProvider.new_default_chain()

    @staticmethod
    def default_client_id() -> str:
        return "test-" + str(uuid4())

    @staticmethod
    def default_iot_endpoint() -> str:
        client = boto3.client("iot")
        response = client.describe_endpoint(endpointType="iot:Data-ATS")
        return response["endpointAddress"]

    def get_connection(self):
        return mqtt_connection_builder.websockets_with_default_aws_signing(
            endpoint=self._endpoint,
            region=self._region,
            credentials_provider=self.credentials_provider(),
            on_connection_interrupted=self.on_connection_interrupted,
            on_connection_resumed=self.on_connection_resumed,
            client_id=self._client_id,
            clean_session=self._clean_session,
            keep_alive_secs=self._keep_alive_secs,
        )

    def on_connection_interrupted(self, connection, error, **kwargs):
        pass

    def on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        pass


class DevClient(AWSIotConnection):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._connection: mqtt.Connection = self.get_connection()

    def connect(self) -> None:
        connect_future = self._connection.connect()
        connect_future.result()

    def subscribe(
        self,
        topic: str,
        on_msg_received: Callable,
        qos: mqtt.QoS = mqtt.QoS.AT_LEAST_ONCE,
    ) -> None:
        subscribe_future, _ = self._connection.subscribe(
            topic=topic, qos=qos, callback=on_msg_received
        )
        subscribe_future.result()

    def unsubscribe(self, topic: str) -> None:
        self._connection.unsubscribe(topic=topic)

    def disconnect(self) -> None:
        disconnect_future = self._connection.disconnect()
        disconnect_future.result()

    def publish(
        self,
        topic,
        payload: dict,
        qos: mqtt.QoS = mqtt.QoS.AT_LEAST_ONCE,
        retain: bool = False,
    ):
        future, *rest = self._connection.publish(
            topic=topic, payload=json.dumps(payload), qos=qos, retain=retain
        )

        return future
