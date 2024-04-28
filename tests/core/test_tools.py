from unittest.mock import Mock, patch, MagicMock
from fluxional.core.tools import Event, Websocket, LookupKey, Environment
import os


def test_env():
    with patch.object(
        os,
        "environ",
        {
            LookupKey.dynamodb_table_name: "some-table",
            LookupKey.api_path_prefix: "/prod",
            LookupKey.websocket_api_id: "some-id",
            LookupKey.websocket_stage_name: "some-stage",
            LookupKey.handler_context: "development",
            LookupKey.event_queue_url: "some-url",
            "AWS_ACCESS_KEY_ID": "some-key",
            "AWS_SECRET_ACCESS_KEY": "some-secret",
            "AWS_SESSION_TOKEN": "some-token",
            "AWS_DEFAULT_REGION": "us-east-1",
        },
    ):
        env = Environment()
        assert env.dynamodb_table_name == "some-table"
        assert env.api_path_prefix == "/prod"
        assert env.websocket_api_id == "some-id"
        assert env.websocket_stage_name == "some-stage"
        assert env.fluxional_handler_context == "development"
        assert env.aws_access_key_id == "some-key"
        assert env.aws_secret_access_key == "some-secret"
        assert env.aws_session_token == "some-token"
        assert env.aws_region == "us-east-1"
        assert env.event_queue_url == "some-url"


@patch("boto3.client")
def test_trigger(mocked_client):
    # Create a mock SQS client
    mock_sqs = Mock()
    mocked_client.return_value = mock_sqs

    # Mock Environment
    with patch("fluxional.core.tools.Environment") as MockEnvironment:
        MockEnvironment.return_value.aws_region = "us-west-2"
        MockEnvironment.return_value.event_queue_url = (
            "http://localhost:4576/queue/test"
        )

        # Create the Event object and trigger an event
        event = Event()
        event.trigger("test_event", {"key": "value"})

    # Assert that the SQS client's send_message method was called with the correct arguments
    mock_sqs.send_message.assert_called_once_with(
        QueueUrl="http://localhost:4576/queue/test",
        MessageBody='{"event_name": "test_event", "data": {"key": "value"}}',
    )


@patch("boto3.client")
def test_post_to_connection(mock_boto3_client):
    # Arrange
    mock_post_to_connection = MagicMock()
    mock_boto3_client.return_value = MagicMock(
        post_to_connection=mock_post_to_connection
    )
    event = {
        "requestContext": {
            "connectionId": "test-connection-id",
            "domainName": "test-domain-name",
            "stage": "test-stage",
        }
    }
    data = "test-data"

    # Act
    Websocket.post_to_connection(event, data)

    # Assert
    mock_boto3_client.assert_called_once_with(
        "apigatewaymanagementapi", endpoint_url="https://test-domain-name/test-stage"
    )
    mock_post_to_connection.assert_called_once_with(
        Data=data, ConnectionId="test-connection-id"
    )
