import os


def default_aws_account_id() -> str:
    AWS_ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID")

    if not AWS_ACCOUNT_ID:
        raise ValueError("AWS_ACCOUNT_ID environment variable is required")

    return AWS_ACCOUNT_ID


def default_aws_region():
    AWS_REGION = os.environ.get("AWS_REGION")

    if not AWS_REGION:
        raise ValueError("AWS_REGION environment variable is required")

    return AWS_REGION


def default_aws_access_key_id() -> str:
    AWS_SECRET_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")

    if not AWS_SECRET_KEY_ID:
        raise ValueError("AWS_SECRET_KEY_ID environment variable is required")

    return AWS_SECRET_KEY_ID


def default_aws_secret_access_key() -> str:
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

    if not AWS_SECRET_ACCESS_KEY:
        raise ValueError("AWS_SECRET_ACCESS_KEY environment variable is required")

    return AWS_SECRET_ACCESS_KEY
