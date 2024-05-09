from fluxional.core.app import App
from fluxional.core.settings import Settings


def test_app_build_api_resources():
    app = App(settings=Settings(stack_name="SomeStack"))

    app.set_api()

    x = app.build_resources(as_dict=True)

    assert x == {
        "fluxional_api_lambda": {
            "id": "fluxional_api_lambda",
            "resource_type": "lambda_function",
            "permissions": [],
            "existing_resource": False,
            "function_name": "somestack_fluxional_api_lambda",
            "directory": "./",
            "dockerfile": "Dockerfile",
            "memory_size": 128,
            "timeout": 30,
            "description": "",
        },
        "fluxional_api_gateway": {
            "id": "fluxional_api_gateway",
            "resource_type": "api_gateway",
            "permissions": [
                {
                    "resource_id": "fluxional_api_lambda",
                    "resource_type": "lambda_function",
                    "allow_invoke": True,
                    "permission_type": "lambda_permission",
                }
            ],
            "existing_resource": False,
            "rest_api_name": "somestack_fluxional_api_gateway",
            "description": "fluxional_api_gateway",
            "endpoint_type": "regional",
            "deploy": True,
            "stage_name": "prod",
            "allowed_methods": [],
            "allowed_origins": [],
            "allowed_credentials": False,
            "allowed_headers": [],
            "rest_api_id": None,
            "root_resource_id": None,
        },
    }


def test_websocket():
    app = App(settings=Settings(stack_name="SomeStack"))

    app.websocket.add_connect_route()
    app.websocket.add_disconnect_route()
    app.websocket.add_default_route()

    assert app.websocket.routes == [
        "$connect",
        "$disconnect",
        "$default",
    ]

    x = app.build_resources(as_dict=True)

    assert x == {
        "fluxional_websocket_lambda": {
            "id": "fluxional_websocket_lambda",
            "resource_type": "lambda_function",
            "existing_resource": False,
            "function_name": "somestack_fluxional_websocket_lambda",
            "directory": "./",
            "dockerfile": "Dockerfile",
            "memory_size": 128,
            "timeout": 30,
            "description": "",
            "permissions": [
                {
                    "allow_publish": True,
                    "permission_type": "websocket_permission",
                    "resource_id": "fluxional_websocket_gateway",
                    "resource_type": "ws_gateway",
                }
            ],
        },
        "fluxional_websocket_gateway": {
            "id": "fluxional_websocket_gateway",
            "websocket_name": "somestack_fluxional_websocket_gateway",
            "resource_type": "ws_gateway",
            "permissions": [
                {
                    "resource_id": "fluxional_websocket_lambda",
                    "resource_type": "lambda_function",
                    "allow_invoke": True,
                    "permission_type": "lambda_permission",
                }
            ],
            "existing_resource": False,
            "stage_name": "prod",
            "auto_deploy": True,
            "routes": [
                "$connect",
                "$disconnect",
                "$default",
            ],
        },
    }


def test_websocket_with_db():
    settings = Settings(
        stack_name="SomeStack",
    )

    settings.permissions.allow_websockets_to_read_from_db = True
    settings.permissions.allow_websockets_to_write_to_db = True

    app = App(settings=settings)

    app.websocket.add_connect_route()
    app.websocket.add_disconnect_route()
    app.websocket.add_default_route()

    app.add_dynamodb()

    x = app.build_resources(as_dict=True)

    assert x == {
        "fluxional_dynamodb": {
            "id": "fluxional_dynamodb",
            "resource_type": "dynamodb",
            "permissions": [],
            "existing_resource": False,
            "partition_key": {"key_name": "pk", "key_type": "string"},
            "sort_key": {"key_name": "sk", "key_type": "string"},
            "stream": "new_image",
            "billing_mode": "pay_per_request",
            "remove_on_delete": True,
            "local_secondary_indexes": [],
            "global_secondary_indexes": [],
        },
        "fluxional_websocket_lambda": {
            "id": "fluxional_websocket_lambda",
            "resource_type": "lambda_function",
            "existing_resource": False,
            "function_name": "somestack_fluxional_websocket_lambda",
            "directory": "./",
            "dockerfile": "Dockerfile",
            "memory_size": 128,
            "timeout": 30,
            "description": "",
            "permissions": [
                {
                    "resource_id": "fluxional_dynamodb",
                    "resource_type": "dynamodb",
                    "allow_read": True,
                    "allow_write": True,
                    "permission_type": "dynamodb_permission",
                },
                {
                    "allow_publish": True,
                    "permission_type": "websocket_permission",
                    "resource_id": "fluxional_websocket_gateway",
                    "resource_type": "ws_gateway",
                },
            ],
        },
        "fluxional_websocket_gateway": {
            "id": "fluxional_websocket_gateway",
            "websocket_name": "somestack_fluxional_websocket_gateway",
            "resource_type": "ws_gateway",
            "permissions": [
                {
                    "resource_id": "fluxional_websocket_lambda",
                    "resource_type": "lambda_function",
                    "allow_invoke": True,
                    "permission_type": "lambda_permission",
                }
            ],
            "existing_resource": False,
            "stage_name": "prod",
            "auto_deploy": True,
            "routes": [
                "$connect",
                "$disconnect",
                "$default",
            ],
        },
    }


def test_storage():
    settings = Settings(
        stack_name="SomeStack",
    )

    settings.storage.enable = True

    app = App(settings=settings)

    app.add_storage_bucket(
        bucket_name="my-bucket",
    )

    x = app.build_resources(as_dict=True)

    assert "fluxional_storage_bucket" in x

    x = app.build_resources(as_dict=True)

    assert "fluxional_storage_lambda" in x
    assert x["fluxional_storage_bucket"]["permissions"] == [
        {
            "resource_id": "fluxional_storage_lambda",
            "resource_type": "lambda_function",
            "allow_invoke": True,
            "permission_type": "lambda_permission",
        }
    ]


def test_storage_api_crud():
    settings = Settings(
        stack_name="SomeStack",
    )

    settings.permissions.allow_api_to_read_from_storage = True
    settings.permissions.allow_api_to_write_to_storage = True
    settings.permissions.allow_api_to_delete_from_storage = True
    settings.storage.enable = True

    app = App(settings=settings)

    app.add_storage_bucket(
        bucket_name="my-bucket",
    )

    app.set_api()

    x = app.build_resources(as_dict=True)

    assert x["fluxional_api_lambda"]["permissions"] == [
        {
            "resource_id": "fluxional_storage_bucket",
            "resource_type": "s3_bucket",
            "allow_read": True,
            "allow_write": True,
            "allow_delete": True,
            "permission_type": "s3_permission",
        }
    ]


def test_rate_schedule():
    settings = Settings(
        stack_name="SomeStack",
    )

    app = App(settings=settings)

    app.schedule.rate_schedule.append(
        {
            "schedule_name": "my_schedule",
            "value": 1,
            "unit": "minute",
        }
    )

    x = app.build_resources(as_dict=True)

    assert x == {
        "fluxional_rate_schedule_task_lambda": {
            "id": "fluxional_rate_schedule_task_lambda",
            "resource_type": "lambda_function",
            "permissions": [],
            "existing_resource": False,
            "function_name": "somestack_fluxional_rate_schedule_task_lambda",
            "directory": "./",
            "dockerfile": "Dockerfile",
            "memory_size": 128,
            "timeout": 30,
            "description": "",
        },
        "somestack_my_schedule": {
            "id": "somestack_my_schedule",
            "resource_type": "rate_schedule",
            "permissions": [
                {
                    "resource_id": "fluxional_rate_schedule_task_lambda",
                    "resource_type": "lambda_function",
                    "allow_invoke": True,
                    "permission_type": "lambda_permission",
                }
            ],
            "existing_resource": False,
            "schedule_name": "my_schedule",
            "value": 1,
            "unit": "minute",
        },
    }


def test_cron_schedule():
    settings = Settings(
        stack_name="SomeStack",
    )

    app = App(settings=settings)

    app.schedule.cron_schedule.append(
        {
            "schedule_name": "my_schedule",
            "minute": "1",
            "hour": "2",
            "day": "3",
            "month": "4",
            "week_day": None,
            "year": "6",
        }
    )

    x = app.build_resources(as_dict=True)

    assert x == {
        "fluxional_cron_schedule_task_lambda": {
            "id": "fluxional_cron_schedule_task_lambda",
            "resource_type": "lambda_function",
            "permissions": [],
            "existing_resource": False,
            "function_name": "somestack_fluxional_cron_schedule_task_lambda",
            "directory": "./",
            "dockerfile": "Dockerfile",
            "memory_size": 128,
            "timeout": 30,
            "description": "",
        },
        "somestack_my_schedule": {
            "id": "somestack_my_schedule",
            "resource_type": "cron_schedule",
            "permissions": [
                {
                    "resource_id": "fluxional_cron_schedule_task_lambda",
                    "resource_type": "lambda_function",
                    "allow_invoke": True,
                    "permission_type": "lambda_permission",
                }
            ],
            "existing_resource": False,
            "schedule_name": "my_schedule",
            "minute": "1",
            "hour": "2",
            "day": "3",
            "month": "4",
            "week_day": None,
            "year": "6",
        },
    }


def test_add_event():
    settings = Settings(
        stack_name="SomeStack",
    )

    app = App(settings=settings)

    app.event.active = True

    x = app.build_resources(as_dict=True)

    assert x == {
        "fluxional_event_lambda": {
            "id": "fluxional_event_lambda",
            "resource_type": "lambda_function",
            "permissions": [],
            "existing_resource": False,
            "function_name": "somestack_fluxional_event_lambda",
            "directory": "./",
            "dockerfile": "Dockerfile",
            "memory_size": 128,
            "timeout": 30,
            "description": "",
        },
        "fluxional_event_queue": {
            "id": "fluxional_event_queue",
            "resource_type": "sqs_queue",
            "permissions": [
                {
                    "resource_id": "fluxional_event_lambda",
                    "resource_type": "lambda_function",
                    "allow_invoke": True,
                    "permission_type": "lambda_permission",
                }
            ],
            "existing_resource": False,
            "queue_name": "somestack_fluxional_event_queue",
            "visibility_timeout": 30,
        },
    }


def test_storage_permissions():
    settings = Settings(
        stack_name="SomeStack",
    )

    # Storage
    settings.storage.enable = True
    settings.permissions.allow_api_to_read_from_storage = True
    settings.permissions.allow_api_to_write_to_storage = True
    settings.permissions.allow_api_to_delete_from_storage = True
    settings.permissions.allow_websockets_to_read_from_storage = True
    settings.permissions.allow_websockets_to_write_to_storage = True
    settings.permissions.allow_websockets_to_delete_from_storage = True
    settings.permissions.allow_events_to_read_from_storage = True
    settings.permissions.allow_events_to_write_to_storage = True
    settings.permissions.allow_events_to_delete_from_storage = True
    settings.permissions.allow_tasks_to_read_from_storage = True
    settings.permissions.allow_tasks_to_write_to_storage = True
    settings.permissions.allow_tasks_to_delete_from_storage = True

    app = App(settings=settings)

    # Websocket
    app.websocket.add_connect_route()

    # Api
    app.set_api()

    # Tasks
    app.schedule.rate_schedule.append(
        {
            "schedule_name": "my_schedule",
            "value": 1,
            "unit": "minute",
        }
    )
    app.schedule.cron_schedule.append(
        {
            "schedule_name": "my_schedule",
            "minute": "1",
            "hour": "2",
            "day": "3",
            "month": "4",
            "week_day": None,
            "year": "6",
        }
    )

    # events
    app.event.active = True

    x = app.build_resources(as_dict=True)

    # Check that each of the lambdas have the correct permissions
    for k in [
        "fluxional_api_lambda",
        "fluxional_rate_schedule_task_lambda",
        "fluxional_cron_schedule_task_lambda",
        "fluxional_event_lambda",
        "fluxional_websocket_lambda",
    ]:
        assert x[k]["permissions"][0]["allow_read"]
        assert x[k]["permissions"][0]["allow_write"]
        assert x[k]["permissions"][0]["allow_delete"]

    # Defaults to false
    assert x["fluxional_storage_lambda"]["permissions"] == []
    assert x["fluxional_storage_lambda"]["permissions"] == []
    assert x["fluxional_storage_lambda"]["permissions"] == []

    settings.permissions.allow_storage_to_write_to_storage = True
    settings.permissions.allow_storage_to_read_from_storage = True
    settings.permissions.allow_storage_to_delete_from_storage = True

    x = app.build_resources(as_dict=True)
    # storage_lambda should now have the permission
    assert x["fluxional_storage_lambda"]["permissions"][0]["allow_read"]
    assert x["fluxional_storage_lambda"]["permissions"][0]["allow_write"]
    assert x["fluxional_storage_lambda"]["permissions"][0]["allow_delete"]


def test_events_permissions():
    settings = Settings(
        stack_name="SomeStack",
    )

    # Storage
    settings.storage.enable = True

    # Events
    settings.permissions.allow_api_to_run_events = True
    settings.permissions.allow_websockets_to_run_events = True
    settings.permissions.allow_storage_to_run_events = True
    settings.permissions.allow_tasks_to_run_events = True

    app = App(settings=settings)

    # Websocket
    app.websocket.add_connect_route()

    # Api
    app.set_api()

    # Tasks
    app.schedule.rate_schedule.append(
        {
            "schedule_name": "my_schedule",
            "value": 1,
            "unit": "minute",
        }
    )
    app.schedule.cron_schedule.append(
        {
            "schedule_name": "my_schedule",
            "minute": "1",
            "hour": "2",
            "day": "3",
            "month": "4",
            "week_day": None,
            "year": "6",
        }
    )

    # events
    app.event.active = True

    x = app.build_resources(as_dict=True)

    # Check that each of the lambdas have the correct permissions
    for k in [
        "fluxional_api_lambda",
        "fluxional_rate_schedule_task_lambda",
        "fluxional_cron_schedule_task_lambda",
        "fluxional_websocket_lambda",
        "fluxional_storage_lambda",
    ]:
        assert x[k]["permissions"][0]["allow_publish"]

    # Defaults to false
    assert x["fluxional_event_lambda"]["permissions"] == []
    assert x["fluxional_event_lambda"]["permissions"] == []
    assert x["fluxional_event_lambda"]["permissions"] == []

    settings.permissions.allow_events_to_run_events = True

    x = app.build_resources(as_dict=True)
    # storage_lambda should now have the permission
    assert x["fluxional_event_lambda"]["permissions"][0]["allow_publish"]


def test_db_permissions():
    settings = Settings(
        stack_name="SomeStack",
    )

    # Storage
    settings.storage.enable = True
    settings.permissions.allow_api_to_read_from_db = True
    settings.permissions.allow_api_to_write_to_db = True
    settings.permissions.allow_websockets_to_read_from_db = True
    settings.permissions.allow_websockets_to_write_to_db = True
    settings.permissions.allow_events_to_read_from_db = True
    settings.permissions.allow_events_to_write_to_db = True
    settings.permissions.allow_tasks_to_read_from_db = True
    settings.permissions.allow_tasks_to_write_to_db = True
    settings.permissions.allow_storage_to_read_from_db = True
    settings.permissions.allow_storage_to_write_to_db = True

    app = App(settings=settings)

    # Add db
    app.add_dynamodb()

    # Api
    app.set_api()

    # Websocket
    app.websocket.add_connect_route()

    # Tasks
    app.schedule.rate_schedule.append(
        {
            "schedule_name": "my_schedule",
            "value": 1,
            "unit": "minute",
        }
    )
    app.schedule.cron_schedule.append(
        {
            "schedule_name": "my_schedule",
            "minute": "1",
            "hour": "2",
            "day": "3",
            "month": "4",
            "week_day": None,
            "year": "6",
        }
    )

    # events
    app.event.active = True

    x = app.build_resources(as_dict=True)

    # Check that each of the lambdas have the correct permissions
    # Since read/write to db is always true it should be ok
    for k in [
        "fluxional_api_lambda",
        "fluxional_rate_schedule_task_lambda",
        "fluxional_cron_schedule_task_lambda",
        "fluxional_event_lambda",
        "fluxional_websocket_lambda",
        "fluxional_storage_lambda",
    ]:
        assert x[k]["permissions"][0]["allow_read"]
        assert x[k]["permissions"][0]["allow_write"]
