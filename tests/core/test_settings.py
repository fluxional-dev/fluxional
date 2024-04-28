from fluxional import Fluxional
from fluxional.core.settings import Settings


def test_settings():
    flux = Fluxional("Test")

    assert flux._settings.credentials.aws_access_key_id is None

    settings = Settings()

    settings.credentials.aws_access_key_id = "aws_access_key_id"

    flux.set_settings(settings)

    # Check that the stack name matches
    assert flux._stack_name == flux._settings.stack_name

    # Check that app settings has updated
    assert flux._app.settings.credentials.aws_access_key_id == "aws_access_key_id"

    # Test that handler settings has updated
    assert flux._handlers._settings.credentials.aws_access_key_id == "aws_access_key_id"
