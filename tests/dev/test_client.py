from fluxional.dev.client import AWSIotConnection, mqtt, DevClient
from unittest.mock import MagicMock, patch
from awscrt import auth


def test_aws_iot_connection():
    connection = AWSIotConnection(
        endpoint="a1b2c3d4e5f6g7-ats.iot.us-east-1.amazonaws.com"
    )
    assert isinstance(connection.default_client_id(), str)
    assert isinstance(
        connection.credentials_provider(),
        auth.AwsCredentialsProvider,
    )
    assert isinstance(connection.get_connection(), mqtt.Connection)
    assert connection.on_connection_interrupted(None, None) is None
    assert connection.on_connection_resumed(None, None, None) is None

    with patch("boto3.client") as mock_boto3_client:
        # Create a mock response
        mock_response = {"endpointAddress": "test_endpoint"}

        # Create a mock client with a mock describe_endpoint method
        mock_client = MagicMock()
        mock_client.describe_endpoint.return_value = mock_response
        mock_boto3_client.return_value = mock_client

        # Call the function
        result = connection.default_iot_endpoint()

        # Assert that the client was created with the correct arguments
        mock_boto3_client.assert_called_once_with("iot")

        # Assert that describe_endpoint was called with the correct arguments
        mock_client.describe_endpoint.assert_called_once_with(
            endpointType="iot:Data-ATS"
        )

        # Assert that the function returned the correct result
        assert result == mock_response["endpointAddress"]


def test_dev_client():
    with patch(
        "awsiot.mqtt_connection_builder.websockets_with_default_aws_signing"
    ) as mock:
        # Create a DevClient instance
        dev_client = DevClient(endpoint="test_endpoint")

        mock.return_value.subscribe.return_value = MagicMock(), None
        mock.return_value.publish.return_value = MagicMock(), None

        dev_client.connect()
        mock.return_value.connect.assert_called_once()

        dev_client.subscribe("topic", lambda x: None)
        mock.return_value.subscribe.assert_called_once()

        dev_client.disconnect()
        mock.return_value.disconnect.assert_called_once()

        dev_client.unsubscribe("topic")
        mock.return_value.unsubscribe.assert_called_once()

        dev_client.publish("topic", "payload")
        mock.return_value.publish.assert_called_once()
