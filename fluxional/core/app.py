from dataclasses import dataclass, asdict, field
from .settings import Settings
from .infrastructure.resources import (
    ApiGateway,
    LambdaFunction,
    InfraResources,
    LambdaPermission,
    DynamoDB,
    DynamoDbPermission,
    WsGateway,
    S3Bucket,
    S3Permission,
    RateSchedule,
    CronSchedule,
    SqsQueue,
    SqsPermission,
    AllPermission,
)
from .infrastructure.types import (
    DynamoDBBillingModeT,
    DynamoDBKeyT,
    DynamoDBLsiT,
    DynamoDBStreamT,
    RateDurationUnitT,
    DynamoDBGsiT,
)
from typing import TypedDict


@dataclass(kw_only=True)
class Websocket:
    routes: list[str] = field(default_factory=list)
    websocket_lambda: LambdaFunction | None = None
    websocket_gateway: WsGateway | None = None

    def add_route(self, route: str):
        self.routes.append(route)

    def add_connect_route(self):
        self.add_route("$connect")

    def add_disconnect_route(self):
        self.add_route("$disconnect")

    def add_default_route(self):
        self.add_route("$default")


@dataclass(kw_only=True)
class Api:
    active: bool = False
    api_lambda: LambdaFunction | None = None
    api_gateway: ApiGateway | None = None


@dataclass(kw_only=True)
class Storage:
    active: bool = field(default=False)
    storage_lambda: LambdaFunction | None = None


class _ScheduleRateT(TypedDict):
    value: int | float
    unit: RateDurationUnitT
    schedule_name: str


class _ScheduleCronT(TypedDict):
    schedule_name: str
    day: str | None
    hour: str | None
    minute: str | None
    month: str | None
    week_day: str | None
    year: str | None


@dataclass(kw_only=True)
class Schedule:
    rate_schedule: list[_ScheduleRateT] = field(default_factory=list)
    cron_schedule: list[_ScheduleCronT] = field(default_factory=list)
    rate_schedule_lambda: LambdaFunction | None = None
    cron_schedule_lambda: LambdaFunction | None = None


@dataclass(kw_only=True)
class Event:
    active: bool = False
    event_lambda: LambdaFunction | None = None
    event_queue: SqsQueue | None = None


@dataclass(kw_only=True)
class App:
    websocket: Websocket = field(default_factory=Websocket)
    database: DynamoDB | None = None
    storage_bucket: S3Bucket | None = None
    settings: Settings
    ##
    api: Api = field(default_factory=Api)
    storage: Storage = field(default_factory=Storage)
    schedule: Schedule = field(default_factory=Schedule)
    event: Event = field(default_factory=Event)

    def _build_api(self, stack_name: str, resources: InfraResources):
        # Check
        if not self.api.active:
            return

        # Resources
        api_lambda = LambdaFunction(
            id=self.settings.system.default_api_lambda_id,
            function_name=f"{stack_name}_{self.settings.system.default_api_lambda_id}",
            existing_resource=False,
            **asdict(self.settings.build.api_lambda),
        )

        api_gateway = ApiGateway(
            id=self.settings.system.default_api_gateway_id,
            rest_api_name=f"{stack_name}_{self.settings.system.default_api_gateway_id}",
            **asdict(self.settings.build.api_gateway),
        )

        api_gateway.permissions.append(
            LambdaPermission(
                resource_id=api_lambda.id,
                resource_type=api_lambda.resource_type,
                allow_invoke=True,
            )
        )

        # Register
        resources[api_lambda.id] = api_lambda
        resources[api_gateway.id] = api_gateway
        self.api.api_lambda = api_lambda
        self.api.api_gateway = api_gateway

    def _build_db(self, stack_name: str, resources: InfraResources):
        if not self.database:
            return

        resources[self.database.id] = self.database

    def _build_websockets(self, stack_name: str, resources: InfraResources):
        # Check
        if not self.websocket.routes:
            return

        # Resources
        websocket_lambda = LambdaFunction(
            id=self.settings.system.default_websocket_lambda_id,
            function_name=f"{stack_name}_{self.settings.system.default_websocket_lambda_id}",
        )

        websocket_api_gateway = WsGateway(
            id=self.settings.system.default_websocket_gateway_id,
            routes=self.websocket.routes,
            websocket_name=f"{stack_name}_{self.settings.system.default_websocket_gateway_id}",
            stage_name=self.settings.build.websocket.stage_name,
            auto_deploy=self.settings.build.websocket.auto_deploy,
        )

        websocket_api_gateway.permissions.append(
            LambdaPermission(
                resource_id=websocket_lambda.id,
                resource_type=websocket_lambda.resource_type,
                allow_invoke=True,
            )
        )

        # Register
        resources[websocket_lambda.id] = websocket_lambda
        resources[websocket_api_gateway.id] = websocket_api_gateway
        self.websocket.websocket_gateway = websocket_api_gateway
        self.websocket.websocket_lambda = websocket_lambda

    def _build_storage(self, stack_name: str, resources: InfraResources):

        # @TODO: May need to refractor the whole storage workflow
        # Check
        if not self.settings.storage.enable and not self.storage.active:
            return

        # Resources
        self.add_storage_bucket(remove_on_delete=self.settings.storage.remove_on_delete)

        if isinstance(self.storage_bucket, S3Bucket):
            resources[self.storage_bucket.id] = self.storage_bucket

            storage_lambda = LambdaFunction(
                id=self.settings.system.default_storage_lambda_id,
                function_name=f"{stack_name}_{self.settings.system.default_storage_lambda_id}",
                existing_resource=False,
                **asdict(self.settings.build.storage_lambda),
            )

            self.storage_bucket.permissions.append(
                LambdaPermission(
                    resource_id=storage_lambda.id,
                    resource_type=storage_lambda.resource_type,
                    allow_invoke=True,
                )
            )

            # Register
            resources[storage_lambda.id] = storage_lambda
            self.storage.storage_lambda = storage_lambda

    def _build_rate_scheduled_tasks(self, stack_name: str, resources: InfraResources):

        # Check
        if not self.schedule.rate_schedule:
            return

        # Resources
        rate_schedules: list[RateSchedule] = []

        for sch in self.schedule.rate_schedule:
            schedule_name = sch["schedule_name"]
            value = sch["value"]
            unit = sch["unit"]

            rate_schedules.append(
                RateSchedule(
                    id=f"{stack_name}_{schedule_name}",
                    schedule_name=schedule_name,
                    value=value,
                    unit=unit,
                )
            )

        lambda_ = LambdaFunction(
            id=self.settings.system.default_rate_schedule_task_lambda_id,
            function_name=f"{stack_name}_{self.settings.system.default_rate_schedule_task_lambda_id}",
            existing_resource=False,
            **asdict(self.settings.build.scheduled_task_lambda),
        )

        for schedule in rate_schedules:
            schedule.permissions.append(
                LambdaPermission(
                    resource_id=lambda_.id,
                    resource_type=lambda_.resource_type,
                    allow_invoke=True,
                )
            )

            # Register
            resources[schedule.id] = schedule

        # Register
        resources[lambda_.id] = lambda_
        self.schedule.rate_schedule_lambda = lambda_

    def _build_cron_scheduled_tasks(self, stack_name: str, resources: InfraResources):
        # Check
        if not self.schedule.cron_schedule:
            return

        # Resources
        cron_schedules: list[CronSchedule] = []

        for sch in self.schedule.cron_schedule:
            schedule_name = sch["schedule_name"]
            day = sch["day"]
            hour = sch["hour"]
            minute = sch["minute"]
            month = sch["month"]
            week_day = sch["week_day"]
            year = sch["year"]

            cron_schedules.append(
                CronSchedule(
                    id=f"{stack_name}_{schedule_name}",
                    schedule_name=schedule_name,
                    day=day,
                    hour=hour,
                    minute=minute,
                    month=month,
                    week_day=week_day,
                    year=year,
                )
            )

        lambda_ = LambdaFunction(
            id=self.settings.system.default_cron_schedule_task_lambda_id,
            function_name=f"{stack_name}_{self.settings.system.default_cron_schedule_task_lambda_id}",
            existing_resource=False,
            **asdict(self.settings.build.scheduled_task_lambda),
        )

        for schedule in cron_schedules:
            schedule.permissions.append(
                LambdaPermission(
                    resource_id=lambda_.id,
                    resource_type=lambda_.resource_type,
                    allow_invoke=True,
                )
            )

            # Register
            resources[schedule.id] = schedule

        # Register
        resources[lambda_.id] = lambda_
        self.schedule.cron_schedule_lambda = lambda_

    def _build_events(self, stack_name: str, resources: InfraResources):
        # Check
        if not self.event.active:
            return

        # Resources
        event_lambda = LambdaFunction(
            id=self.settings.system.default_event_lambda_id,
            function_name=f"{stack_name}_{self.settings.system.default_event_lambda_id}",
            existing_resource=False,
            **asdict(self.settings.build.event_lambda),
        )

        queue = SqsQueue(
            id=self.settings.system.default_event_queue_id,
            queue_name=f"{stack_name}_{self.settings.system.default_event_queue_id}",
            # Visibility Timeout cannot be less than the lambda timeout
            visibility_timeout=self.settings.build.event_lambda.timeout,
        )

        queue.permissions.append(
            LambdaPermission(
                resource_id=event_lambda.id,
                resource_type=event_lambda.resource_type,
                allow_invoke=True,
            )
        )

        # Register
        resources[event_lambda.id] = event_lambda
        resources[queue.id] = queue
        self.event.event_lambda = event_lambda
        self.event.event_queue = queue

    @staticmethod
    def _append_permission_if_allowed(
        entity: LambdaFunction | None,
        permission: AllPermission,
        attributes: dict[str, bool],
    ):
        if entity and any(attributes.values()):
            for k, v in attributes.items():
                setattr(permission, k, v)
            entity.permissions.insert(0, permission)

    def _build_db_permissions(self):
        ## DYNAMODB PERMISSIONS ##
        if self.database and isinstance(self.database, DynamoDB):
            permission = DynamoDbPermission(
                resource_id=self.database.id,
                resource_type=self.database.resource_type,
                allow_read=False,
                allow_write=False,
            )

            # -> API
            self._append_permission_if_allowed(
                self.api.api_lambda,
                permission,
                {
                    "allow_read": self.settings.permissions.allow_api_to_read_from_db,
                    "allow_write": self.settings.permissions.allow_api_to_write_to_db,
                },
            )

            # -> WEBSOCKETS
            self._append_permission_if_allowed(
                self.websocket.websocket_lambda,
                permission,
                {
                    "allow_read": self.settings.permissions.allow_websockets_to_read_from_db,
                    "allow_write": self.settings.permissions.allow_websockets_to_write_to_db,
                },
            )
            # -> STORAGE
            self._append_permission_if_allowed(
                self.storage.storage_lambda,
                permission,
                {
                    "allow_read": self.settings.permissions.allow_storage_to_read_from_db,
                    "allow_write": self.settings.permissions.allow_storage_to_write_to_db,
                },
            )

            # -> ASYNC EVENTS
            self._append_permission_if_allowed(
                self.event.event_lambda,
                permission,
                {
                    "allow_read": self.settings.permissions.allow_events_to_read_from_db,
                    "allow_write": self.settings.permissions.allow_events_to_write_to_db,
                },
            )

            # -> TASKS
            self._append_permission_if_allowed(
                self.schedule.rate_schedule_lambda,
                permission,
                {
                    "allow_read": self.settings.permissions.allow_tasks_to_read_from_db,
                    "allow_write": self.settings.permissions.allow_tasks_to_write_to_db,
                },
            )

            self._append_permission_if_allowed(
                self.schedule.cron_schedule_lambda,
                permission,
                {
                    "allow_read": self.settings.permissions.allow_tasks_to_read_from_db,
                    "allow_write": self.settings.permissions.allow_tasks_to_write_to_db,
                },
            )

    def _build_storage_permissions(self):
        if not self.storage_bucket:
            return

        permission = S3Permission(
            resource_id=self.storage_bucket.id,
            resource_type=self.storage_bucket.resource_type,
            allow_read=False,
            allow_write=False,
            allow_delete=False,
        )

        # -> API
        self._append_permission_if_allowed(
            self.api.api_lambda,
            permission,
            {
                "allow_read": self.settings.permissions.allow_api_to_read_from_storage,
                "allow_write": self.settings.permissions.allow_api_to_write_to_storage,
                "allow_delete": self.settings.permissions.allow_api_to_delete_from_storage,
            },
        )

        # -> WEBSOCKETS
        self._append_permission_if_allowed(
            self.websocket.websocket_lambda,
            permission,
            {
                "allow_read": self.settings.permissions.allow_websockets_to_read_from_storage,
                "allow_write": self.settings.permissions.allow_websockets_to_write_to_storage,
                "allow_delete": self.settings.permissions.allow_websockets_to_delete_from_storage,
            },
        )

        # -> STORAGE
        self._append_permission_if_allowed(
            self.storage.storage_lambda,
            permission,
            {
                "allow_read": self.settings.permissions.allow_storage_to_read_from_storage,
                "allow_write": self.settings.permissions.allow_storage_to_write_to_storage,
                "allow_delete": self.settings.permissions.allow_storage_to_delete_from_storage,
            },
        )
        # -> EVENTS
        self._append_permission_if_allowed(
            self.event.event_lambda,
            permission,
            {
                "allow_read": self.settings.permissions.allow_events_to_read_from_storage,
                "allow_write": self.settings.permissions.allow_events_to_write_to_storage,
                "allow_delete": self.settings.permissions.allow_events_to_delete_from_storage,
            },
        )

        # -> TASKS
        self._append_permission_if_allowed(
            self.schedule.rate_schedule_lambda,
            permission,
            {
                "allow_read": self.settings.permissions.allow_tasks_to_read_from_storage,
                "allow_write": self.settings.permissions.allow_tasks_to_write_to_storage,
                "allow_delete": self.settings.permissions.allow_tasks_to_delete_from_storage,
            },
        )

        self._append_permission_if_allowed(
            self.schedule.cron_schedule_lambda,
            permission,
            {
                "allow_read": self.settings.permissions.allow_tasks_to_read_from_storage,
                "allow_write": self.settings.permissions.allow_tasks_to_write_to_storage,
                "allow_delete": self.settings.permissions.allow_tasks_to_delete_from_storage,
            },
        )

    def _build_events_permissions(self):
        if not self.event.event_queue:
            return

        permission = SqsPermission(
            resource_id=self.event.event_queue.id,
            resource_type=self.event.event_queue.resource_type,
            allow_publish=True,
        )

        # -> API
        self._append_permission_if_allowed(
            self.api.api_lambda,
            permission,
            {"allow_publish": self.settings.permissions.allow_api_to_run_events},
        )

        # -> WEBSOCKETS
        self._append_permission_if_allowed(
            self.websocket.websocket_lambda,
            permission,
            {"allow_publish": self.settings.permissions.allow_websockets_to_run_events},
        )

        # -> STORAGE
        self._append_permission_if_allowed(
            self.storage.storage_lambda,
            permission,
            {"allow_publish": self.settings.permissions.allow_storage_to_run_events},
        )

        # -> EVENTS
        self._append_permission_if_allowed(
            self.event.event_lambda,
            permission,
            {"allow_publish": self.settings.permissions.allow_events_to_run_events},
        )

        # -> TASKS
        self._append_permission_if_allowed(
            self.schedule.rate_schedule_lambda,
            permission,
            {"allow_publish": self.settings.permissions.allow_tasks_to_run_events},
        )

        self._append_permission_if_allowed(
            self.schedule.cron_schedule_lambda,
            permission,
            {"allow_publish": self.settings.permissions.allow_tasks_to_run_events},
        )

    def build_resources(
        self, as_dict: bool = False
    ) -> InfraResources | dict[str, dict]:
        """
        Build the infrastructure resources
        """
        resources: InfraResources = {}
        stack_name = self.settings.stack_name.lower()

        procedures = [
            ## Database ##
            self._build_db,
            ## API ##
            self._build_api,
            ## Websocket ##
            self._build_websockets,
            ## S3 ##
            self._build_storage,
            ## Scheduled Tasks ##
            self._build_rate_scheduled_tasks,
            self._build_cron_scheduled_tasks,
            ## Events ##
            self._build_events,
        ]

        permissions = [
            self._build_db_permissions,
            self._build_storage_permissions,
            self._build_events_permissions,
        ]

        for procedure in procedures:
            procedure(stack_name, resources)

        for permission in permissions:
            permission()

        if as_dict:
            return {k: asdict(v) for k, v in resources.items()}

        return resources

    def add_dynamodb(
        self,
        partition_key: DynamoDBKeyT | None = None,
        sort_key: DynamoDBKeyT | None = None,
        remove_on_delete: bool = True,
        local_secondary_indexes: list[DynamoDBLsiT] | None = None,
        global_secondary_indexes: list[DynamoDBGsiT] | None = None,
        # @NOTE Not currently supported
        stream: DynamoDBStreamT | None = None,
        billing_mode: DynamoDBBillingModeT | None = None,
    ) -> None:
        """
        Add a DynamoDB table to the application
        """

        dynamodb = DynamoDB(
            id=self.settings.system.default_dynamodb_id,
            partition_key=partition_key
            or self.settings.build.dynamodb.default_primary_key,
            sort_key=sort_key or self.settings.build.dynamodb.default_secondary_key,
            remove_on_delete=remove_on_delete,
            stream=stream or self.settings.build.dynamodb.default_stream,
            billing_mode=billing_mode
            or self.settings.build.dynamodb.default_billing_mode,
            local_secondary_indexes=local_secondary_indexes or [],
            global_secondary_indexes=global_secondary_indexes or [],
        )

        self.database = dynamodb

    def add_storage_bucket(
        self,
        bucket_name: str | None = None,
        remove_on_delete: bool = True,
    ) -> None:
        """
        Add an Storage bucket to the application
        """

        safe = lambda x: x.replace("_", "-").lower()  # noqa

        storage_bucket = S3Bucket(
            id=self.settings.system.default_storage_bucket_id,
            bucket_name=(
                bucket_name
                if bucket_name
                else safe(self.settings.stack_name)
                + safe(self.settings.system.default_storage_bucket_id)
            ),
            remove_on_delete=remove_on_delete,
        )

        self.storage_bucket = storage_bucket

    def set_api(self):
        self.api.active = True
