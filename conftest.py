import pytest
from uuid import uuid4


@pytest.fixture()
def random_id():
    return str(uuid4())
