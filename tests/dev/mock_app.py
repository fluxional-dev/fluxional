def handler(event, context):
    return {
        "statusCode": 200,
        "body": "hello world",
    }


def handler_with_error(event, context):
    raise Exception("Error")
