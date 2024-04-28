from fluxional.utils import (
    default_aws_access_key_id,
    default_aws_account_id,
    default_aws_region,
    default_aws_secret_access_key,
)

import pytest


def test_that_default_aws_account_id_raises_value_error_when_not_set():
    with pytest.raises(ValueError):
        default_aws_account_id()


def test_that_default_aws_region_raises_value_error_when_not_set():
    with pytest.raises(ValueError):
        default_aws_region()


def test_that_default_aws_access_key_id_raises_value_error_when_not_set():
    with pytest.raises(ValueError):
        default_aws_access_key_id()


def test_that_default_aws_secret_access_key_raises_value_error_when_not_set():
    with pytest.raises(ValueError):
        default_aws_secret_access_key()
