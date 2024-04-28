from fluxional.core.events import (
    is_http_event,
    is_sns_event,
    is_fluxional_event,
    is_websocket_event,
    is_dev_context,
    is_s3_bucket_create_event,
    is_s3_bucket_delete_event,
    is_eventbridge_scheduled_event,
    is_rate_schedule_event,
    is_cron_schedule_event,
    is_sqs_event,
)
from fluxional.core.tools import LookupKey
from unittest.mock import patch
import os


def test_is_sqs_event():
    assert is_sqs_event(
        {
            "Records": [
                {
                    "eventSource": "aws:sqs",
                }
            ]
        },
        {},
    )
    assert not is_sqs_event(
        {
            "Records": [
                {
                    "eventSource": "aws:not_sqs",
                }
            ]
        },
        {},
    )
    assert not is_sqs_event({}, {})


def test_is_http_event():
    assert is_http_event({"httpMethod": "GET"}, {})
    assert not is_http_event({"not_httpMethod": "GET"}, {})


def test_is_rate_schedule():
    assert is_rate_schedule_event(
        {
            "schedule_type": "RateSchedule",
        },
        {},
    )
    assert not is_rate_schedule_event(
        {
            "not_schedule_type": "RateSchedule",
        },
        {},
    )


def test_is_cron_schedule():
    assert is_cron_schedule_event(
        {
            "schedule_type": "CronSchedule",
        },
        {},
    )
    assert not is_cron_schedule_event(
        {
            "not_schedule_type": "CronSchedule",
        },
        {},
    )


def test_is_sns_event():
    assert is_sns_event(
        {
            "Records": [
                {
                    "EventSource": "aws:sns",
                }
            ]
        },
        {},
    )
    assert not is_sns_event(
        {
            "Records": [
                {
                    "EventSource": "aws:not_sns",
                }
            ]
        },
        {},
    )
    assert not is_sns_event({}, {})

    assert is_fluxional_event({"fluxional_event": "cli_deploy"}, {})

    assert not is_fluxional_event({"not-event": "cli_sync"}, {})


def test_is_websocket_event():
    assert is_websocket_event(
        {
            "requestContext": {
                "routeKey": "$connect",
            }
        },
        {},
    )
    assert not is_websocket_event(
        {
            "requestContext": {
                "not_routeKey": "$connect",
            }
        },
        {},
    )
    assert not is_websocket_event({}, {})


def test_is_dev_context():
    with patch.object(
        os,
        "environ",
        {LookupKey.handler_context: "development"},
    ):
        assert is_dev_context(
            {
                "httpMethod": "GET",
            },
            {},
        )
    with patch.object(
        os,
        "environ",
        {LookupKey.handler_context: "production"},
    ):
        assert not is_dev_context(
            {
                "httpMethod": "GET",
            },
            {},
        )


def test_s3_events():
    assert is_s3_bucket_create_event(
        {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "eventName": "ObjectCreated:Put",
                }
            ]
        },
        {},
    )
    assert not is_s3_bucket_create_event(
        {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "eventName": "ObjectRemoved:Put",
                }
            ]
        },
        {},
    )
    assert not is_s3_bucket_create_event({}, {})

    assert is_s3_bucket_delete_event(
        {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "eventName": "ObjectRemoved:Delete",
                }
            ]
        },
        {},
    )
    assert not is_s3_bucket_delete_event(
        {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "eventName": "ObjectCreated:Delete",
                }
            ]
        },
        {},
    )
    assert not is_s3_bucket_delete_event({}, {})


def test_is_eventbridge_scheduled_event():
    event = {
        "version": "0",
        "account": "123456789012",
        "region": "us-east-2",
        "detail": {},
        "detail-type": "Scheduled Event",
        "source": "aws.events",
        "time": "2019-03-01T01:23:45Z",
        "id": "cdc73f9d-aea9-11e3-9d5a-835b769c0d9c",
        "resources": ["arn:aws:events:us-east-2:123456789012:rule/my-schedule"],
    }

    assert is_eventbridge_scheduled_event(event, {})

    event = {
        "version": "0",
        "account": "123456789012",
        "region": "us-east-2",
        "detail": {},
        "detail-type": "Not",
    }

    assert not is_eventbridge_scheduled_event(event, {})
