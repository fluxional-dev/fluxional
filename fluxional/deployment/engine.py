from .exceptions import (
    FailedImageBuild,
    FailedContainerBuild,
    FailedToRunContainer,
)
from .constants import (
    DID_VOLUME,
    BASE_WORKDIR,
    BASE_IMAGE,
    CDK_DEPLOY_CMD,
    CDK_DESTROY_CMD,
    AWS_LAMBDA_PYTHON_3_10_IMAGE,
    RUNTIMES,
    OTEL_WRAPPER_FILE,
    OTEL_INST_FILE,
    OTEL_REQ_FILE,
    FTE_EXTENSION,
)
import docker  # type: ignore
import os
import json
from dotenv import load_dotenv
from fluxional.utils import (
    default_aws_account_id,
    default_aws_region,
    default_aws_secret_access_key,
    default_aws_access_key_id,
)
from rich.console import Console
from rich import print as rp
from typing import Any, Literal
from fluxional import __version__
import re


load_dotenv()

# Fix that will avoid using fileobject which does not allow
# Context - IE: Imposible to copy files from host to container
docker.api.build.process_dockerfile = lambda file, _: (
    "Dockerfile",
    file,
)

console = Console()

RuntimeT = Literal["3.10", "3.11", "3.12"]

_Container = type[docker.models.containers.Container]


def st(process: Any, description: str, *args, **kwargs):
    with console.status(description):
        output = process(*args, **kwargs)

    if isinstance(output, list):
        output_key_info(output)


def output_key_info(logs: list[str]):
    # Currently only extracts API Gateway Endpoints
    rp("\n[underline bold yellow]Outputs:")

    for log in logs:
        http_url_pattern = r"https://[a-zA-Z0-9./-]+"
        ws_url_pattern = r"wss://[a-zA-Z0-9./-]+"

        http_match = re.search(http_url_pattern, log)
        ws_match = re.search(ws_url_pattern, log)

        if http_match:
            api_endpoint = http_match.group()
            rp(f"\n👉 [bold yellow] API Endpoint: {api_endpoint}")

        if ws_match:
            websocket_url = ws_match.group()
            rp(f"\n👉 [bold yellow] WebSocket URL: {websocket_url}")


def track_logs(container: _Container) -> list[str]:
    logs: list[str] = []
    output_logs: list[str] = []

    for line in container.logs(stream=True):
        log = line.decode("utf-8").strip()
        if log:
            logs.append(log)
            if log == "Outputs:":
                output_logs.append(log)
            elif output_logs:
                output_logs.append(log)
            else:
                print(log)

    try:
        container_exit_code = container.wait()["StatusCode"]
        if container_exit_code != 0:
            for log in logs:
                rp(log)
            raise FailedContainerBuild("The container failed to build.")
    except docker.errors.NotFound:  # pragma: no cover
        pass

    return output_logs


class Engine:
    def __init__(
        self,
        *,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_account_id: str | None = None,
        aws_region: str | None = None,
        base_url: str = "unix://var/run/docker.sock",
        tag: str = "fluxional_deploy_image",
        build_path: str = os.getcwd(),
        remove_container: bool = False,
    ):
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._aws_account_id = aws_account_id
        self._aws_region = aws_region
        self._tag = tag
        self._build_path = build_path
        self._remove_container = remove_container
        self._api_client = docker.APIClient(base_url=base_url)
        self._client = docker.from_env()
        self.setup_credentials()

    def setup_credentials(self):
        if not self._aws_access_key_id:
            self._aws_access_key_id = default_aws_access_key_id()

        if not self._aws_secret_access_key:
            self._aws_secret_access_key = default_aws_secret_access_key()

        if not self._aws_account_id:
            self._aws_account_id = default_aws_account_id()

        if not self._aws_region:
            self._aws_region = default_aws_region()

    def build_image(
        self,
        dockerfile: str,
        tag: str | None = None,
        show_logs: bool = False,
        rm: bool = True,
    ):
        """
        Builds the docker image given a dockerfile like strings
        """

        def display(row: Any):
            if "errorDetail" in row:
                row = json.loads(row)["errorDetail"]["message"]
                rp(f"[red]{row}")
                raise FailedImageBuild(row)

            elif '"stream"' in row:
                row = json.loads(row)
                if row["stream"] != "\n":
                    row = row["stream"].replace("\n", "")
                    if show_logs:
                        print(row)

        build = self._api_client.build(
            dockerfile=dockerfile,
            rm=rm,
            tag=tag or self._tag,
            path=self._build_path,
        )

        for line in build:
            row = line.decode("utf-8").strip()

            # Windows specific
            if "\r\n" in row:
                row = row.split("\r\n")

                for row in row:
                    display(row)

            else:
                display(row)

    def run_container(
        self,
        *,
        command: str,
        volumes: dict[str, dict[str, str]] = DID_VOLUME,
        environment: dict[str, str] = {},
        tag: str | None = None,
        detach: bool = False,
        show_logs: bool = False,
        network_mode: Literal["host", "bridge", "none"] = "bridge",
    ) -> list[str]:
        """
        Runs the built image given a command
        """

        try:
            container = self._client.containers.run(
                tag or self._tag,
                remove=True,
                auto_remove=self._remove_container,
                detach=detach,
                volumes=volumes,
                environment={
                    "AWS_ACCESS_KEY_ID": self._aws_access_key_id,
                    "AWS_SECRET_ACCESS_KEY": self._aws_secret_access_key,
                    "AWS_ACCOUNT_ID": self._aws_account_id,
                    "AWS_REGION": self._aws_region,
                }
                | environment,
                command=command,
                network_mode=network_mode,
            )

        except Exception as e:
            raise FailedToRunContainer(e)

        if not detach and show_logs:
            if isinstance(container, bytes):
                rp("\n[bold blue] Container Ouptut:\n")
                container = container.decode("utf-8")
                print(container)
                return []

        if detach and show_logs:
            return track_logs(container)

        else:
            return []

    def remove_built_image(self, tag: str | None = None, **kwargs):
        """
        Removes the built image from the docker daemon
        """

        try:
            self._client.images.remove(tag or self._tag, **kwargs)
        except docker.errors.ImageNotFound:
            pass

    def image_exists(self):
        """
        Check if the image exists
        """
        try:
            self._client.images.get(self._tag)
            return True
        except docker.errors.ImageNotFound:
            return False


class CDKEngine(Engine):
    @staticmethod
    def build_dep_copy(
        dependencies: list[str], *, copy_directory=".", work_directory=BASE_WORKDIR
    ) -> str:
        """
        Build the command COPY based on a list of dependencies
        """
        deps = [f"COPY {copy_directory}/{k} {work_directory}/{k}" for k in dependencies]

        return "\n".join(deps)

    def get_dockerfile(
        self,
        *,
        dependencies=list[str],
        requirements_file: str | None = None,
        base_image: str = BASE_IMAGE,
        work_directory: str = BASE_WORKDIR,
    ) -> str:
        """
        Create a dockerfile based on dependencies etc...
        """
        base_image = f"FROM {base_image}"
        work_dir = f"WORKDIR {work_directory}"
        dockerfile = f"{base_image}"

        if dependencies:
            files = self.build_dep_copy(dependencies, work_directory=work_directory)
            dockerfile += f"\n{files}"

        dockerfile += f"\n{work_dir}"

        if requirements_file:
            dockerfile += f"\nRUN pip install -r {requirements_file}"

        dockerfile += "\n"

        return dockerfile

    def get_otel_steps(self) -> str:
        # Download the otel files and install requirements
        dockerfile = f"\nRUN curl -sSL {OTEL_INST_FILE} -o /opt/otel-instrument"
        dockerfile += "\nRUN chmod +x /opt/otel-instrument"
        dockerfile += f"\nRUN curl -sSL {OTEL_REQ_FILE} -o requirements_otel.txt"
        dockerfile += "\nRUN pip install -r requirements_otel.txt --target /opt/python"
        dockerfile += (
            f"\nRUN curl -sSL {OTEL_WRAPPER_FILE} -o /opt/python/otel_wrapper.py"
        )
        return dockerfile

    def get_fte_steps(self) -> str:
        dockerfile = "\nRUN pip install requests"
        dockerfile += "\nRUN yum install -y unzip"
        dockerfile += f"\nRUN curl -sSL {FTE_EXTENSION} -o ./python-example-telemetry-api-extension.zip"
        dockerfile += "\nRUN unzip ./python-example-telemetry-api-extension.zip -d ./python-example-telemetry-api-extension"
        # Copy content to /opt
        dockerfile += "\nRUN cp -r ./python-example-telemetry-api-extension/python-example-telemetry-api-extension/* /opt/"
        # Remove the zip file
        dockerfile += "\nRUN rm ./python-example-telemetry-api-extension.zip"
        # Remove the folder
        dockerfile += "\nRUN rm -rf ./python-example-telemetry-api-extension"

        return dockerfile

    def get_lambda_dockefile(
        self,
        *,
        lambda_handler: str,
        base_image: str = AWS_LAMBDA_PYTHON_3_10_IMAGE,
        requirements_file: str | None = None,
        include_otel: bool = False,
        include_fte: bool = False,
    ):
        dockerfile = f"FROM {base_image}"

        dockerfile += "\nCOPY . \${LAMBDA_TASK_ROOT}"

        if requirements_file:
            dockerfile += (
                f"\nRUN pip install -r {requirements_file}"
                # Needs to be escaped once for the echo cmd
                + r' --target "\${LAMBDA_TASK_ROOT}"'
            )
        else:
            # We will always need fluxional installed
            dockerfile += (
                f"\nRUN pip install fluxional=={__version__}"
                + r' --target "\${LAMBDA_TASK_ROOT}"'
            )

        if include_otel:
            dockerfile += self.get_otel_steps()

        if include_fte:
            dockerfile += self.get_fte_steps()

        dockerfile += f'\nCMD [\\"{lambda_handler}\\"]'

        return dockerfile

    def run_clean(
        self,
        *,
        dependencies: list[str],
        requirements_file: str | None,
        handler: str,
        command: str,
        environment: dict[str, str],
        lambda_handler: str | None = None,
        show_logs: bool,
        base_image: str = AWS_LAMBDA_PYTHON_3_10_IMAGE,
        include_otel: bool = False,
        include_fte: bool = False,
    ):
        dockerfile = self.get_dockerfile(
            dependencies=dependencies, requirements_file=requirements_file
        )

        # We need to add the lambda Dockefile for cdk here
        lambda_dockerfile = self.get_lambda_dockefile(
            lambda_handler=lambda_handler if lambda_handler else handler,
            requirements_file=requirements_file,
            base_image=base_image,
            include_otel=include_otel,
            include_fte=include_fte,
        )

        for line in lambda_dockerfile.split("\n"):
            dockerfile += f'RUN echo "{line}" >> Dockerfile\n'

        st(self.build_image, "[blue]Building image", dockerfile, show_logs=show_logs)

        # Run the container
        st(
            self.run_container,
            "[blue]Deploying changes",
            command=command,
            environment=environment,
            show_logs=show_logs,
            detach=True,
        )

        # Always clean the image
        st(self.remove_built_image, "[blue]Cleaning up", force=True)

    def run(
        self,
        handler: str,
        *,
        command: str,
        dependencies: list[str],
        requirements_file: str | None,
        environment: dict[str, str] = {},
        lambda_handler: str | None = None,
        lambda_runtime: RuntimeT = "3.10",
        show_logs: bool = False,
        include_otel: bool = False,
        include_fte: bool = False,
    ):
        rp("\n\n[bold blue]Fluxional CDK Engine \U0001F680\n")

        # We need to include certain mandatory files to auto-copy
        # For the file name
        file_name = handler.split(".")[0]
        if f"{file_name}.py" not in dependencies:
            dependencies.append(f"{file_name}.py")

        # For requirements
        if requirements_file and requirements_file not in dependencies:
            dependencies.append(requirements_file)

        rp("[bold]Configurations:")
        rp(f"Show logs: {show_logs}")
        rp(f"Dependencies: {dependencies}")
        rp(f"Runtime: Python {lambda_runtime}")

        self.run_clean(
            dependencies=dependencies,
            requirements_file=requirements_file,
            handler=lambda_handler if lambda_handler else handler,
            command=command,
            environment=environment,
            lambda_handler=lambda_handler,
            show_logs=show_logs,
            base_image=RUNTIMES[lambda_runtime],
            include_otel=include_otel,
            include_fte=include_fte,
        )

        rp("\n\n[bold blue]  \U0001F680 Change Completed! \U0001F680 \n\n")

    def deploy(
        self,
        handler: str,
        *,
        command: str | None = None,
        dependencies: list[str] = [],
        requirements_file: str | None = "requirements.txt",
        environment: dict[str, str] = {},
        lambda_handler: str | None = None,
        lambda_runtime: RuntimeT = "3.10",
        show_logs: bool = False,
        include_otel: bool = False,
        include_fte: bool = False,
    ):
        file_name, _ = handler.split(".")

        if not command:
            command = CDK_DEPLOY_CMD.format(app=f"{file_name}.py")

        self.run(
            handler,
            command=command,
            dependencies=dependencies,
            requirements_file=requirements_file,
            environment=environment,
            lambda_handler=lambda_handler,
            show_logs=show_logs,
            lambda_runtime=lambda_runtime,
            include_otel=include_otel,
            include_fte=include_fte,
        )

    def destroy(
        self,
        handler: str,
        *,
        command: str | None = None,
        dependencies: list[str] = [],
        requirements_file: str | None = "requirements.txt",
        environment: dict[str, str] = {},
        lambda_handler: str | None = None,
        lambda_runtime: RuntimeT = "3.10",
        show_logs: bool = False,
    ):
        file_name, _ = handler.split(".")

        if not command:
            command = CDK_DESTROY_CMD.format(app=f"{file_name}.py")

        self.run(
            handler,
            command=command,
            dependencies=dependencies,
            requirements_file=requirements_file,
            environment=environment,
            lambda_handler=lambda_handler,
            show_logs=show_logs,
            lambda_runtime=lambda_runtime,
        )
