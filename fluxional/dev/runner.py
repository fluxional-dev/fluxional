from fluxional.deployment.engine import Engine
from fluxional.deployment.constants import AWS_LAMBDA_PYTHON_3_10_IMAGE
import os


class FunctionEngine(Engine):
    def setup_credentials(self):
        pass


def build_launcher(handler: str) -> str:
    file, module = handler.split(".")

    code = [f"from {file} import {module}"]
    code.append("from fluxional.dev.client import DevClient")
    code.append("import os")
    code.append("import json")
    code.append(r"client = DevClient()")
    code.append(r"client.connect()")
    code.append(r"event = json.loads(os.environ.get('EVENT'))")
    code.append(r"event_id = os.environ.get('EVENT_ID')")
    code.append(r"print('EVENT_ID: ', event_id)")
    code.append(r"subscriber_id = os.environ.get('SUBSCRIBER_ID')")
    code.append(r"print('Acknowledging event...')")
    code.append(
        r"x = client.publish(f'fluxional/acknowledge/{event_id}', {'subscriber_id': subscriber_id})"
    )
    code.append(r"x.result(timeout=5)")
    code.append(r"print('Event acknowledged')")
    code.append("try:")
    code.append(rf"    result = {module}(event, None)")
    code.append(r"except Exception as e:")
    code.append(r"    print('ERROR:', e)")
    code.append(r"    result = {'statusCode': 500, 'body': 'Internal Server Error'}")
    code.append(r"print(result)")
    code.append(r"print('Sending response...')")
    code.append(
        r"x = client.publish(f'fluxional/response/{event_id}', {'subscriber_id': subscriber_id, 'response': result})"
    )
    code.append(r"x.result(timeout=5)")
    code.append(r"print('Response sent')")
    code.append(r"client.disconnect()")

    return "\\n".join(code)


def build_runner_image(
    stack_name: str,
    handler: str,
    *,
    requirements_file: str | None = "requirements.txt",
    build_path: str = ".",
    engine_provider: type[FunctionEngine] = FunctionEngine,
):
    dockerfile = f"FROM {AWS_LAMBDA_PYTHON_3_10_IMAGE}"

    dockerfile += "\nWORKDIR /"

    if requirements_file:
        dockerfile += f"\nCOPY {requirements_file} ."
        dockerfile += f"\nRUN pip install -r {requirements_file}"

    # Remove the default entrypoint
    dockerfile += "\nENTRYPOINT []"
    # Create the launcher file
    launcher = build_launcher(handler)
    dockerfile += f'\n RUN echo -e "{launcher}" >> launcher.py'
    dockerfile += "\nENV PYTHONPATH /app"
    stack_name = stack_name.lower()
    tag = f"{stack_name}_local_runner"
    engine = engine_provider(tag=tag, build_path=build_path, remove_container=False)
    engine.build_image(dockerfile, show_logs=True)


def run(
    stack_name: str,
    command: str = "python3 launcher.py",
    build_path: str = ".",
    environment: dict = {},
    engine_provider: type[FunctionEngine] = FunctionEngine,
):
    # Mout the current directory to /app
    mount_path = os.path.join(os.getcwd(), build_path)
    mount_volume = {mount_path: {"bind": "/app", "mode": "ro"}}

    engine = engine_provider(
        tag=f"{stack_name.lower()}_local_runner",
        build_path=build_path,
        remove_container=False,
    )

    if engine.image_exists():
        engine.run_container(
            command=command,
            detach=True,
            show_logs=True,
            volumes=mount_volume,
            environment=environment,
            network_mode="host",
        )

    return
