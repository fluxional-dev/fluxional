from .resources import (
    InfraSettings,
    InfrastructureT,
    LambdaFunction,
    ApiGateway,
    WsGateway,
    AllResources,
    DynamoDB,
    ResourceTypeGuard,
    SnsTopic,
    parse_dict_to_resources,
    S3Bucket,
    RateSchedule,
    CronSchedule,
    SqsQueue,
)
from .cdk import (
    add_lambda_function_to_stack,
    add_existing_rest_api_gateway_to_stack,
    add_rest_api_gateway_to_stack,
    add_dynamodb_to_stack,
    add_sns_topic_to_stack,
    add_ws_gateway_to_stack,
    add_s3_bucket_to_stack,
    add_rate_schedule_to_stack,
    add_cron_schedule_to_stack,
    add_sqs_queue_to_stack,
)
from aws_cdk import (
    Stack as CDKStack,
    App,
    Environment,
    aws_apigateway,
    aws_iam,
    aws_lambda,
    aws_sns_subscriptions,
    aws_s3_notifications,
    aws_events_targets,
    aws_events,
    aws_sqs,
    aws_s3,
    aws_lambda_event_sources,
)
from aws_cdk.aws_apigatewayv2_integrations_alpha import WebSocketLambdaIntegration
from aws_cdk.aws_apigatewayv2 import WebSocketApi
from fluxional.exceptions import MissingStackResource
from fluxional.utils import default_aws_account_id, default_aws_region
from fluxional.core.tools import LookupKey


class Stack(CDKStack):
    def __init__(
        self,
        stack_name: str,
        *,
        aws_account_id: str,
        aws_region: str,
        environment_vars: dict = {},
    ):
        self._stack_name = stack_name
        self._aws_account_id = aws_account_id
        self._aws_region = aws_region
        self._environment_vars = environment_vars
        self._environment = Environment(account=aws_account_id, region=aws_region)
        self._app = App()
        super().__init__(self._app, self._stack_name, env=self._environment)

    @property
    def app(self) -> App:
        return self._app

    def add_sqs_queue(self, resource: SqsQueue):
        queue = add_sqs_queue_to_stack(
            stack=self,
            id=resource.id,
            queue_name=resource.queue_name,
            visibility_timeout=resource.visibility_timeout,
        )

        if resource.permissions:
            for k in resource.permissions:
                if ResourceTypeGuard.is_lambda_permission(k):

                    if k.allow_invoke:
                        func: aws_lambda.Function = getattr(self, k.resource_id)

                        source = aws_lambda_event_sources.SqsEventSource(
                            queue,
                            batch_size=1,
                        )
                        func.add_event_source(source)

    def add_cron_schedule(self, resource: CronSchedule):
        schedule = add_cron_schedule_to_stack(
            stack=self,
            id=resource.id,
            schedule_name=resource.schedule_name,
            day=resource.day,
            hour=resource.hour,
            minute=resource.minute,
            month=resource.month,
            week_day=resource.week_day,
            year=resource.year,
        )

        if resource.permissions:
            for k in resource.permissions:
                if ResourceTypeGuard.is_lambda_permission(k):
                    if k.allow_invoke:
                        schedule.add_target(
                            aws_events_targets.LambdaFunction(
                                getattr(self, k.resource_id),
                                event=aws_events.RuleTargetInput.from_object(
                                    {
                                        "schedule_type": "CronSchedule",
                                        "schedule_name": resource.schedule_name,
                                    }
                                ),
                            )
                        )

    def add_rate_schedule(self, resource: RateSchedule):
        schedule = add_rate_schedule_to_stack(
            stack=self,
            id=resource.id,
            unit=resource.unit,
            value=resource.value,
            schedule_name=resource.schedule_name,
        )

        if resource.permissions:
            for k in resource.permissions:
                if ResourceTypeGuard.is_lambda_permission(k):
                    if k.allow_invoke:
                        schedule.add_target(
                            aws_events_targets.LambdaFunction(
                                getattr(self, k.resource_id),
                                event=aws_events.RuleTargetInput.from_object(
                                    {
                                        "schedule_type": "RateSchedule",
                                        "schedule_name": resource.schedule_name,
                                    }
                                ),
                            )
                        )

    def add_sns_topic(self, resource: SnsTopic):
        sns = add_sns_topic_to_stack(
            stack=self,
            id=resource.id,
            display_name=resource.display_name,
        )

        if resource.permissions:
            for k in resource.permissions:
                if ResourceTypeGuard.is_lambda_permission(k):
                    if k.allow_invoke:
                        sns.add_subscription(
                            aws_sns_subscriptions.LambdaSubscription(
                                getattr(self, k.resource_id)
                            )
                        )

    def add_lambda_function(self, resource: LambdaFunction):
        lambda_ = add_lambda_function_to_stack(
            stack=self,
            id=resource.id,
            function_name=resource.function_name,
            directory=resource.directory,
            file=resource.dockerfile,
            memory_size=resource.memory_size,
            timeout=resource.timeout,
            description=resource.description,
        )

        # Add environment variables
        if self._environment_vars:
            for k in self._environment_vars:
                lambda_.add_environment(key=k, value=self._environment_vars[k])

                # @DEV - May be refractored to permission in the future
                # Add a policy if the fluxional_handler_context in os
                if k == LookupKey.handler_context:
                    if self._environment_vars[k] == "development":
                        lambda_.add_to_role_policy(
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=["iot:Connect"],
                                resources=["*"],
                            )
                        )
                        lambda_.add_to_role_policy(
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=["iot:Publish", "iot:Receive"],
                                resources=["arn:aws:iot:*:*:topic/fluxional*"],
                            )
                        )
                        lambda_.add_to_role_policy(
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=["iot:Subscribe"],
                                resources=["arn:aws:iot:*:*:topicfilter/fluxional*"],
                            )
                        )
                        lambda_.add_to_role_policy(
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=["iot:DescribeEndpoint"],
                                resources=["*"],
                            )
                        )

        # Add the resource id
        lambda_.add_environment(LookupKey.resource_id, resource.id)

        # Add the execution context to cloud
        lambda_.add_environment(LookupKey.execution_context, "cloud")

        if resource.permissions:
            for k in resource.permissions:
                if ResourceTypeGuard.is_dynamodb_permission(k):
                    if k.allow_read:
                        getattr(self, k.resource_id).grant_read_data(lambda_)

                    if k.allow_write:
                        getattr(self, k.resource_id).grant_write_data(lambda_)

                    lambda_.add_environment(
                        k.resource_id + "_table_name",
                        getattr(self, k.resource_id).table_name or "",
                    )

                elif ResourceTypeGuard.is_sns_permission(k):
                    if k.allow_publish:
                        sns = getattr(self, k.resource_id)

                        sns_policy = aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["sns:Publish"],
                            resources=[
                                sns.topic_arn,
                            ],
                        )

                        lambda_.add_to_role_policy(sns_policy)

                        lambda_.add_environment(
                            k.resource_id + "_topic_arn",
                            getattr(self, k.resource_id).topic_arn or "",
                        )

                elif ResourceTypeGuard.is_websocket_permission(k):
                    if k.allow_publish:
                        ws: WebSocketApi = getattr(self, k.resource_id)

                        # Create a policy statement that allows invoking the @connections POST endpoint
                        policy_statement = aws_iam.PolicyStatement(
                            actions=["execute-api:ManageConnections"],
                            resources=[
                                f"arn:aws:execute-api:*:*:{ws.api_id}/*/@connections/*"
                            ],
                        )

                        # Attach the policy statement to the Lambda function's execution role
                        lambda_.add_to_role_policy(policy_statement)

                        # put the webocket api @connections url in the environment

                        lambda_.add_environment(
                            k.resource_id + "_api_id",
                            ws.api_id,
                        )

                elif ResourceTypeGuard.is_s3_permission(k):
                    bucket: aws_s3.Bucket = getattr(self, k.resource_id)

                    if any([k.allow_read, k.allow_write, k.allow_delete]):
                        lambda_.add_environment(
                            k.resource_id + "_bucket_name",
                            bucket.bucket_name or "",
                        )

                    if k.allow_read:
                        bucket.grant_read(lambda_)

                    if k.allow_write:
                        bucket.grant_write(lambda_)

                    if k.allow_delete:
                        bucket.grant_delete(lambda_)

                elif ResourceTypeGuard.is_sqs_permission(k):
                    queue: aws_sqs.Queue = getattr(self, k.resource_id)

                    if k.allow_publish:
                        queue.grant_send_messages(lambda_)

                        lambda_.add_environment(
                            k.resource_id + "_queue_url",
                            queue.queue_url or "",
                        )

    def add_websocket_gateway(self, resource: WsGateway):
        gw = add_ws_gateway_to_stack(
            stack=self,
            id=resource.id,
            stage_name=resource.stage_name,
            auto_deploy=resource.auto_deploy,
            websocket_name=resource.websocket_name,
        )

        if len(resource.permissions) > 1:
            raise ValueError("Websocket gateway can only invoke one lambda.")

        if resource.permissions:
            permission = resource.permissions[0]
            if (
                ResourceTypeGuard.is_lambda_permission(permission)
                and permission.allow_invoke
            ):
                func: aws_lambda.Function = getattr(self, permission.resource_id)

                for route in resource.routes:
                    gw.add_route(
                        route,
                        integration=WebSocketLambdaIntegration(
                            route + "_integration", func
                        ),
                    )

                # Allow the invoked functions to have access to @connections
                # Create a policy statement that allows invoking the @connections POST endpoint
                policy_statement = aws_iam.PolicyStatement(
                    actions=["execute-api:ManageConnections"],
                    resources=[f"arn:aws:execute-api:*:*:{gw.api_id}/*/@connections/*"],
                )

                # Attach the policy statement to the Lambda function's execution role
                func.add_to_role_policy(policy_statement)

                # Add stage name and api_id to the environment
                func.add_environment(
                    resource.id + "_api_id",
                    gw.api_id,
                )
                func.add_environment(resource.id + "_stage_name", resource.stage_name)

    def add_rest_api_gateway(self, resource: ApiGateway):
        if resource.existing_resource:
            gw = add_existing_rest_api_gateway_to_stack(
                stack=self,
                id=resource.id,
                rest_api_id=resource.rest_api_id or "",
                root_resource_id=resource.root_resource_id or "",
            )
        else:
            gw = add_rest_api_gateway_to_stack(
                stack=self,
                id=resource.id,
                rest_api_name=resource.rest_api_name,
                description=resource.description,
                endpoint_type=resource.endpoint_type,
                deploy=resource.deploy,
                stage_name=resource.stage_name,
            )

        if resource.permissions:
            for k in resource.permissions:
                if ResourceTypeGuard.is_lambda_permission(k) and k.allow_invoke:
                    func: aws_lambda.Function = getattr(self, k.resource_id)
                    gw.root.add_proxy(
                        any_method=True,
                        default_integration=aws_apigateway.LambdaIntegration(func),
                    )

                    func.grant_invoke(
                        aws_iam.ServicePrincipal("apigateway.amazonaws.com")
                    )

                    # We want to add the stage name as an environment variable
                    # For some api may require it but with the / at the front
                    func.add_environment(
                        LookupKey.api_path_prefix, "/" + resource.stage_name
                    )

    def add_dynamodb(self, resource: DynamoDB):
        add_dynamodb_to_stack(
            stack=self,
            id=resource.id,
            partition_key=resource.partition_key,
            sort_key=resource.sort_key,
            stream=resource.stream,
            billing_mode=resource.billing_mode,
            remove_on_delete=resource.remove_on_delete,
            local_secondary_indexes=resource.local_secondary_indexes,
            global_secondary_indexes=resource.global_secondary_indexes,
        )

    def add_s3_bucket(self, resource: S3Bucket):
        bucket = add_s3_bucket_to_stack(
            stack=self,
            id=resource.id,
            bucket_name=resource.bucket_name,
            remove_on_delete=resource.remove_on_delete,
        )

        if resource.permissions:
            for k in resource.permissions:
                if ResourceTypeGuard.is_lambda_permission(k) and k.allow_invoke:
                    func: aws_lambda.Function = getattr(self, k.resource_id)

                    bucket.add_object_created_notification(
                        aws_s3_notifications.LambdaDestination(func)
                    )

                    bucket.add_object_removed_notification(
                        aws_s3_notifications.LambdaDestination(func)
                    )

                    # This will cause a dependency error and makes no sense if on file upload
                    # The lambda can't even read the file
                    # We will refrain from writing though as that could create infinite loop for now
                    bucket.grant_read(func)

    def add_resource_to_stack(self, resource: AllResources):
        if isinstance(resource, LambdaFunction):
            self.add_lambda_function(resource)
        elif isinstance(resource, ApiGateway):
            self.add_rest_api_gateway(resource)
        elif isinstance(resource, WsGateway):
            self.add_websocket_gateway(resource)
        elif isinstance(resource, DynamoDB):
            self.add_dynamodb(resource)
        elif isinstance(resource, SnsTopic):
            self.add_sns_topic(resource)
        elif isinstance(resource, S3Bucket):
            self.add_s3_bucket(resource)
        elif isinstance(resource, RateSchedule):
            self.add_rate_schedule(resource)
        elif isinstance(resource, CronSchedule):
            self.add_cron_schedule(resource)
        elif isinstance(resource, SqsQueue):
            self.add_sqs_queue(resource)


class Infrastructure:
    def __init__(self, *, infrastructure: InfrastructureT) -> None:
        self._infrastructure = infrastructure

    @property
    def settings(self) -> InfraSettings:
        return self._infrastructure.settings

    @property
    def resources(self) -> dict[str, AllResources]:
        return self._infrastructure.resources

    @classmethod
    def from_dict(cls, value: dict) -> "Infrastructure":
        settings = InfraSettings(**value["settings"])
        resources = value["resources"]
        parsed_resources = parse_dict_to_resources(resources)

        return cls(
            infrastructure=InfrastructureT(
                settings=settings, resources=parsed_resources
            )
        )

    def get_stack(self) -> Stack:
        # This will look environment var if not provided
        return Stack(
            aws_account_id=self.settings.aws_account_id or default_aws_account_id(),
            aws_region=self.settings.aws_region or default_aws_region(),
            stack_name=self.settings.stack_name,
            environment_vars=self.settings.environment,
        )

    def stack(self) -> Stack:
        stack_builder = self.get_stack()
        ready: list[str] = []
        resources = self._infrastructure.resources
        counter = 0
        limit = 500

        # Build each resources based on dependencies resolution
        # Iterate until all resources are built
        while True:
            counter += 1
            left = [
                resources[stack_resource].id
                for stack_resource in resources
                if resources[stack_resource].id not in ready
            ]

            for k in resources:
                resource = resources[k]
                permissions = resource.permissions

                # If resource is already built, skip
                if resource.id in ready:
                    continue

                # Check for permission dependency
                if permissions:
                    for i in permissions:
                        # Raise an error if the permission does not exist
                        # At all anywhere
                        if i.resource_id not in resources:
                            raise MissingStackResource(
                                f"""Resource {i.resource_id} not found in stack"""
                            )

                    # Check if all permission for this resource are resolved
                    if not all([i.resource_id in ready for i in permissions]):
                        continue

                # Add the resource to the base infrastructure
                stack_builder.add_resource_to_stack(resource)
                ready.append(resource.id)

            if counter > limit:
                raise ValueError("Resource dependency loop detected")

            if not left:
                break

        return stack_builder
