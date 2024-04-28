from typing import Literal


def is_http_event(event, context) -> bool:
    if "httpMethod" in event:
        return True

    return False


def is_sns_event(event, context) -> bool:
    if "Records" in event:
        for record in event["Records"]:
            if "EventSource" in record and record["EventSource"] == "aws:sns":
                return True

    return False


def is_fluxional_event(event, context) -> bool:
    if "fluxional_event" in event:
        return True

    return False


def is_websocket_event(event, context) -> str | bool:
    """Check if websocket event and return the route to it"""
    if "requestContext" in event:
        if "routeKey" in event["requestContext"]:
            return event["requestContext"]["routeKey"]

    return False


def is_eventbridge_scheduled_event(event, context) -> bool:
    if "source" in event and event["source"] == "aws.events":
        if "detail-type" in event and event["detail-type"] == "Scheduled Event":
            return True

    return False


def is_rate_schedule_event(event, context) -> bool:
    if "schedule_type" in event and event["schedule_type"] == "RateSchedule":
        return True

    return False


def is_cron_schedule_event(event, context) -> bool:
    if "schedule_type" in event and event["schedule_type"] == "CronSchedule":
        return True

    return False


def is_dev_context(event, context) -> bool:
    """Check if the current context is a realtime lambda"""
    from .tools import Environment

    env = Environment()

    if env.fluxional_handler_context == "development":
        # Only support http events for now
        if is_http_event(event, context):
            return True

    return False


S3_BUCKET_CREATE_EVENTS = [
    "ObjectCreated:*",
    "ObjectCreated:Put",
    "ObjectCreated:Post",
    "ObjectCreated:Copy",
    "ObjectCreated:CompleteMultipartUpload",
]


S3_BUCKET_DELETE_EVENTS = [
    "ObjectRemoved:*",
    "ObjectRemoved:Delete",
    "ObjectRemoved:DeleteMarkerCreated",
]

S3_ACTIONS = Literal["create", "delete"]


def is_s3_bucket_create_event(event, context) -> bool:
    if "Records" in event:
        for record in event["Records"]:
            if "eventSource" in record and record["eventSource"] == "aws:s3":
                if record["eventName"] in S3_BUCKET_CREATE_EVENTS:
                    return True

    return False


def is_s3_bucket_delete_event(event, context) -> bool:
    if "Records" in event:
        for record in event["Records"]:
            if "eventSource" in record and record["eventSource"] == "aws:s3":
                if record["eventName"] in S3_BUCKET_DELETE_EVENTS:
                    return True

    return False


def is_sqs_event(event, context) -> bool:
    if "Records" in event:
        for record in event["Records"]:
            if "eventSource" in record and record["eventSource"] == "aws:sqs":
                return True

    return False
