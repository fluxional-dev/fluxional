infrastructure = {
    "fluxional_api_lambda": {
        "id": "fluxional_api_lambda",
        "resource_type": "lambda_function",
        "permissions": [
            {
                "resource_id": "fluxional_storage_bucket",
                "resource_type": "s3_bucket",
                "allow_read": True,
                "allow_write": True,
                "allow_delete": True,
                "permission_type": "s3_permission",
            },
            {
                "resource_id": "fluxional_event_queue",
                "resource_type": "sqs_queue",
                "allow_publish": True,
                "permission_type": "sqs_permission",
            },
        ],
        "existing_resource": False,
        "function_name": "fluxe2emultifileproject_fluxional_api_lambda",
        "directory": "./",
        "dockerfile": "Dockerfile",
        "memory_size": 128,
        "timeout": 30,
        "description": "fluxional_api_lambda_v1",
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
        "rest_api_name": "fluxe2emultifileproject_fluxional_api_gateway",
        "description": "fluxional_api_gateway_v1",
        "endpoint_type": "regional",
        "deploy": True,
        "stage_name": "v1",
        "allowed_methods": [],
        "allowed_origins": [],
        "allowed_credentials": False,
        "allowed_headers": [],
        "rest_api_id": None,
        "root_resource_id": None,
    },
    "fluxional_websocket_lambda": {
        "id": "fluxional_websocket_lambda",
        "resource_type": "lambda_function",
        "permissions": [],
        "existing_resource": False,
        "function_name": "fluxe2emultifileproject_fluxional_websocket_lambda",
        "directory": "./",
        "dockerfile": "Dockerfile",
        "memory_size": 128,
        "timeout": 30,
        "description": "",
    },
    "fluxional_websocket_gateway": {
        "id": "fluxional_websocket_gateway",
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
        "websocket_name": "fluxe2emultifileproject_fluxional_websocket_gateway",
        "stage_name": "prod",
        "auto_deploy": True,
        "routes": ["$connect"],
    },
    "fluxional_storage_bucket": {
        "id": "fluxional_storage_bucket",
        "resource_type": "s3_bucket",
        "permissions": [
            {
                "resource_id": "fluxional_storage_lambda",
                "resource_type": "lambda_function",
                "allow_invoke": True,
                "permission_type": "lambda_permission",
            }
        ],
        "existing_resource": False,
        "bucket_name": "fluxe2emultifileprojectfluxional-storage-bucket",
        "remove_on_delete": True,
    },
    "fluxional_storage_lambda": {
        "id": "fluxional_storage_lambda",
        "resource_type": "lambda_function",
        "permissions": [],
        "existing_resource": False,
        "function_name": "fluxe2emultifileproject_fluxional_storage_lambda",
        "directory": "./",
        "dockerfile": "Dockerfile",
        "memory_size": 128,
        "timeout": 30,
        "description": "",
    },
    "fluxional_cron_schedule_task_lambda": {
        "id": "fluxional_cron_schedule_task_lambda",
        "resource_type": "lambda_function",
        "permissions": [],
        "existing_resource": False,
        "function_name": "fluxe2emultifileproject_fluxional_cron_schedule_task_lambda",
        "directory": "./",
        "dockerfile": "Dockerfile",
        "memory_size": 128,
        "timeout": 30,
        "description": "",
    },
    "fluxe2emultifileproject_every_minute": {
        "id": "fluxe2emultifileproject_every_minute",
        "resource_type": "rate_schedule",
        "permissions": [
            {
                "resource_id": "fluxional_cron_schedule_task_lambda",
                "resource_type": "lambda_function",
                "allow_invoke": True,
                "permission_type": "lambda_permission",
            }
        ],
        "existing_resource": False,
        "schedule_name": "every_minute",
        "value": 1,
        "unit": "minutes",
    },
    "fluxional_event_lambda": {
        "id": "fluxional_event_lambda",
        "resource_type": "lambda_function",
        "permissions": [],
        "existing_resource": False,
        "function_name": "fluxe2emultifileproject_fluxional_event_lambda",
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
        "queue_name": "fluxe2emultifileproject_fluxional_event_queue",
    },
}

if __name__ == "__main__":
    from main import flux

    assert flux._app.build_resources(as_dict=True) == infrastructure
