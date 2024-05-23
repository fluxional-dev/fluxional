from fluxional.deployment import Engine, CDKEngine
from fluxional.deployment.engine import track_logs, output_key_info
from fluxional.deployment.exceptions import (
    FailedImageBuild,
    FailedContainerBuild,
    FailedToRunContainer,
)
import os
import pytest
from unittest.mock import patch, Mock


def test_image_does_not_exist_raise_no_error(random_id):
    engine = Engine(
        aws_access_key_id="1",
        aws_secret_access_key="1",
        aws_account_id="1",
        aws_region="1",
    )
    assert not engine.remove_built_image(tag=random_id)


def test_engine_hello_world(random_id):
    engine = Engine(
        aws_access_key_id="1",
        aws_secret_access_key="1",
        aws_account_id="1",
        aws_region="1",
        tag=random_id,
    )

    engine.build_image(
        """
FROM alpine:latest
RUN echo "sleep 2" >> hello_world.sh
RUN echo "echo Hello, world!" >> hello_world.sh
RUN echo "python3 xxx.py" >> hello_world.sh
"""
    )

    with pytest.raises(FailedContainerBuild):
        engine.run_container(
            command="/bin/sh ./hello_world.sh",
            detach=True,
            show_logs=True,
        )

    try:
        engine.remove_built_image()
    except:  # noqa
        ...

    # Should simply have outputed the container bytes logs
    engine = Engine(
        aws_access_key_id="1",
        aws_secret_access_key="1",
        aws_account_id="1",
        aws_region="1",
        tag=random_id,
    )

    engine.build_image(
        """
FROM alpine:latest
RUN echo "echo Hello, world!" >> hello_world.sh
"""
    )

    engine.run_container(
        detach=False, show_logs=True, command="/bin/sh ./hello_world.sh"
    )

    engine.remove_built_image()


def test_remove_container(random_id):
    engine = Engine(
        aws_access_key_id="1",
        aws_secret_access_key="1",
        aws_account_id="1",
        aws_region="1",
        tag=random_id,
    )

    engine.build_image(
        """
FROM alpine:latest
RUN echo "echo Sleep 10" >> hello_world.sh
RUN echo "sleep 10" >> hello_world.sh
RUN echo "echo Hello, world!" >> hello_world.sh
"""
    )

    engine.run_container(
        command="/bin/sh ./hello_world.sh", detach=True, show_logs=False
    )

    engine.remove_built_image(force=True)


def test_engine_setup_credentials():
    with patch.object(
        os,
        "environ",
        {
            "AWS_ACCESS_KEY_ID": "1",
            "AWS_SECRET_ACCESS_KEY": "1",
            "AWS_ACCOUNT_ID": "1",
            "AWS_REGION": "1",
        },
    ):
        engine = Engine()

        assert engine._aws_access_key_id == "1"
        assert engine._aws_secret_access_key == "1"
        assert engine._aws_account_id == "1"
        assert engine._aws_region == "1"


def test_that_image_is_built(capfd, random_id):
    engine = Engine(
        aws_access_key_id="1",
        aws_secret_access_key="1",
        aws_account_id="1",
        aws_region="1",
        tag=random_id,
    )

    assert not engine.image_exists()

    engine.build_image(
        """
FROM fluxionality/cdk_deploy:latest
"""
    )
    assert engine.image_exists()
    engine.remove_built_image()


def test_that_exc_is_raised_image_build(random_id):
    engine = Engine(
        aws_access_key_id="1",
        aws_secret_access_key="1",
        aws_account_id="1",
        aws_region="1",
        tag=random_id,
    )

    with pytest.raises(FailedImageBuild):
        engine.build_image(
            """
        FROM hello-world
        COPY non_existent_file /app/non_existent_file
"""
        )


def test_that_container_runs(capfd):
    engine = Engine(
        aws_access_key_id="1",
        aws_secret_access_key="1",
        aws_account_id="1",
        aws_region="1",
    )
    engine.build_image(
        """
FROM fluxionality/cdk_deploy:latest
"""
    )
    engine.run_container(command="cdk --version")
    engine.remove_built_image()


def test_that_exc_is_raised_container_build(random_id):
    engine = Engine(
        aws_access_key_id="1",
        aws_secret_access_key="1",
        aws_account_id="1",
        aws_region="1",
        tag=random_id,
    )

    engine.build_image(
        """
FROM fluxionality/cdk_deploy:latest
"""
    )

    # This fail at the container run level
    with pytest.raises(FailedToRunContainer):
        engine.run_container(command="command_not_found")

    engine.remove_built_image()


def test_cdk_engine_build_dep_copy():
    dep = CDKEngine.build_dep_copy(["main.py", "xyz"])

    exp = """COPY ./main.py /app/main.py
COPY ./xyz /app/xyz"""

    assert dep == exp


def test_cdk_engine_get_dockerfile():
    engine = CDKEngine(
        aws_access_key_id="1",
        aws_secret_access_key="1",
        aws_account_id="1",
        aws_region="1",
    )

    dockerfile = engine.get_dockerfile(
        dependencies=["main.py", "requirements.txt"],
        requirements_file="requirements.txt",
    )

    exp = """FROM fluxionality/cdk_deploy:latest
COPY ./main.py /app/main.py
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
"""

    assert dockerfile == exp


def test_cdk_engine_get_lambda_dockerfile():
    engine = CDKEngine(
        aws_access_key_id="1",
        aws_secret_access_key="1",
        aws_account_id="1",
        aws_region="1",
    )

    dockerfile = engine.get_lambda_dockefile(
        lambda_handler="some_file.handler",
        requirements_file="requirements.txt",
        include_otel=True,
        include_fte=True,
        lambda_dockerfile_ext="""RUN install something""",
    )

    exp = """FROM public.ecr.aws/lambda/python:3.10
COPY . \\${LAMBDA_TASK_ROOT}
RUN install something
RUN pip install -r requirements.txt --target "\\${LAMBDA_TASK_ROOT}"
RUN curl -sSL https://tjaws.s3.amazonaws.com/otel-instrument -o /opt/otel-instrument
RUN chmod +x /opt/otel-instrument
RUN curl -sSL https://tjaws.s3.amazonaws.com/requirements_otel.txt -o requirements_otel.txt
RUN pip install -r requirements_otel.txt --target /opt/python
RUN curl -sSL https://tjaws.s3.amazonaws.com/otel_wrapper.py -o /opt/python/otel_wrapper.py
RUN pip install requests
RUN yum install -y unzip
RUN curl -sSL https://tjaws.s3.amazonaws.com/python-example-telemetry-api-extension.zip -o ./python-example-telemetry-api-extension.zip
RUN unzip ./python-example-telemetry-api-extension.zip -d ./python-example-telemetry-api-extension
RUN cp -r ./python-example-telemetry-api-extension/python-example-telemetry-api-extension/* /opt/
RUN rm ./python-example-telemetry-api-extension.zip
RUN rm -rf ./python-example-telemetry-api-extension
CMD [\\"some_file.handler\\"]"""

    assert exp == dockerfile


def test_cdk_engine_deploy(random_id):
    engine = CDKEngine(
        aws_access_key_id="1",
        aws_secret_access_key="1",
        aws_account_id="1",
        aws_region="1",
        build_path=os.path.join(os.getcwd(), "tests", "deployment"),
        tag=random_id,
    )

    # This fail because we don't have a valid AWS account
    with pytest.raises(FailedContainerBuild):
        engine.deploy(
            "mock_handler.handler",
            dependencies=["mock_handler.py"],
            requirements_file=None,
            show_logs=True,
        )

    engine.remove_built_image(force=True)


def test_cdk_engine_destroy(random_id):
    engine = CDKEngine(
        aws_access_key_id="1",
        aws_secret_access_key="1",
        aws_account_id="1",
        aws_region="1",
        build_path=os.path.join(os.getcwd(), "tests", "deployment"),
        tag=random_id,
    )

    # This fail because we don't have a valid AWS account
    with pytest.raises(FailedContainerBuild):
        engine.destroy(
            "mock_handler.handler",
            dependencies=["mock_handler.py"],
            requirements_file=None,
            show_logs=True,
        )

    engine.remove_built_image(force=True)


def test_engine_run(random_id):
    build_path = "tests/deployment"

    engine = CDKEngine(
        aws_account_id="1234",
        aws_region="us-east-1",
        aws_access_key_id="1234",
        aws_secret_access_key="1234",
        build_path=build_path,
        tag=random_id,
    )

    engine.run(
        "mock_app.handler",
        dependencies=["mock_app.py"],
        requirements_file="mock_req.text",
        command="cdk --version",
        environment={},
        show_logs=True,
    )


def test_otel_steps():
    engine = CDKEngine(
        aws_account_id="1234",
        aws_region="us-east-1",
        aws_access_key_id="1234",
        aws_secret_access_key="1234",
        build_path="tests/deployment",
        tag="dirtyrun_base_image",
    )

    steps = """
RUN curl -sSL https://tjaws.s3.amazonaws.com/otel-instrument -o /opt/otel-instrument
RUN chmod +x /opt/otel-instrument
RUN curl -sSL https://tjaws.s3.amazonaws.com/requirements_otel.txt -o requirements_otel.txt
RUN pip install -r requirements_otel.txt --target /opt/python
RUN curl -sSL https://tjaws.s3.amazonaws.com/otel_wrapper.py -o /opt/python/otel_wrapper.py"""

    assert engine.get_otel_steps() == steps


def test_fte_steps():
    engine = CDKEngine(
        aws_account_id="1234",
        aws_region="us-east-1",
        aws_access_key_id="1234",
        aws_secret_access_key="1234",
        build_path="tests/deployment",
        tag="dirtyrun_base_image",
    )

    steps = """
RUN pip install requests
RUN yum install -y unzip
RUN curl -sSL https://tjaws.s3.amazonaws.com/python-example-telemetry-api-extension.zip -o ./python-example-telemetry-api-extension.zip
RUN unzip ./python-example-telemetry-api-extension.zip -d ./python-example-telemetry-api-extension
RUN cp -r ./python-example-telemetry-api-extension/python-example-telemetry-api-extension/* /opt/
RUN rm ./python-example-telemetry-api-extension.zip
RUN rm -rf ./python-example-telemetry-api-extension"""

    assert engine.get_fte_steps() == steps


def test_track_logs():
    # Mock the _Container object
    container = Mock()

    # Define the logs that the container should return
    container.logs.return_value = [
        b"Log 1",
        b"Outputs:",
        b"https://ct37az2nsf.execute-api.us-east-1.amazonaws.com/v1/",
        b"Log 2",
    ]

    container.wait.return_value = {"StatusCode": 0}

    output_logs = track_logs(container)

    assert output_logs == [
        "Outputs:",
        "https://ct37az2nsf.execute-api.us-east-1.amazonaws.com/v1/",
        "Log 2",
    ]


def test_output_key_info(capsys):
    # Need a console check here
    output_key_info(
        [
            "Outputs:",
            # HTTP
            "https://ct37az2nsf.execute-api.us-east-1.amazonaws.com/v1/",
            # Websocket
            "wss://ct37az2nsf.execute-api.us-east-1.amazonaws.com/v1/",
        ]
    )

    captured = capsys.readouterr()
    assert "https://ct37az2nsf.execute-api.us-east-1.amazonaws.com/v1/" in captured.out
    assert "wss://ct37az2nsf.execute-api.us-east-1.amazonaws.com/v1/" in captured.out
