from typing import TypedDict, Literal, Any, Optional, Dict, List
from typing_extensions import Protocol

_HttpMethods = Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]


## Api Gateway ##
class _RequestContext(TypedDict):
    resourcePath: str
    httpMethod: _HttpMethods
    path: str


class ApiEvent(TypedDict):
    resource: str
    path: str
    httpMethod: _HttpMethods
    requestContext: _RequestContext
    headers: dict
    multiValueHeaders: dict
    queryStringParameters: dict
    multiValueQueryStringParameters: dict
    pathParameters: dict
    stageVariables: dict
    isBase64Encoded: bool
    body: Any


## Lambda Context ##
# https://github.com/jordaneremieff/mangum/blob/main/mangum/types.pys
class LambdaCognitoIdentity(Protocol):
    """Information about the Amazon Cognito identity that authorized the request.

    **cognito_identity_id** - The authenticated Amazon Cognito identity.
    **cognito_identity_pool_id** - The Amazon Cognito identity pool that authorized the
    invocation.
    """

    cognito_identity_id: str
    cognito_identity_pool_id: str


class LambdaMobileClient(Protocol):
    """Mobile client information for the application and the device.

    **installation_id** - A unique identifier for an installation instance of an
    application.
    **app_title** - The title of the application. For example, "My App".
    **app_version_code** - The version of the application. For example, "V2.0".
    **app_version_name** - The version code for the application. For example, 3.
    **app_package_name** - The name of the package. For example, "com.example.my_app".
    """

    installation_id: str
    app_title: str
    app_version_name: str
    app_version_code: str
    app_package_name: str


class LambdaMobileClientContext(Protocol):
    """Information about client application and device when invoked via AWS Mobile SDK.

    **client** - A dict of name-value pairs that describe the mobile client application.
    **custom** - A dict of custom values set by the mobile client application.
    **env** - A dict of environment information provided by the AWS SDK.
    """

    client: LambdaMobileClient
    custom: Dict[str, Any]
    env: Dict[str, Any]


class LambdaContext(Protocol):
    """The context object passed to the handler function.

    **function_name** - The name of the Lambda function.
    **function_version** - The version of the function.
    **invoked_function_arn** - The Amazon Resource Name (ARN) that's used to invoke the
    function. Indicates if the invoker specified a version number or alias.
    **memory_limit_in_mb** - The amount of memory that's allocated for the function.
    **aws_request_id** - The identifier of the invocation request.
    **log_group_name** - The log group for the function.
    **log_stream_name** - The log stream for the function instance.
    **identity** - (mobile apps) Information about the Amazon Cognito identity that
    authorized the request.
    **client_context** - (mobile apps) Client context that's provided to Lambda by the
    client application.
    """

    function_name: str
    function_version: str
    invoked_function_arn: str
    memory_limit_in_mb: int
    aws_request_id: str
    log_group_name: str
    log_stream_name: str
    identity: Optional[LambdaCognitoIdentity]
    client_context: Optional[LambdaMobileClientContext]

    def get_remaining_time_in_millis(self) -> int:
        """Returns the number of milliseconds left before the execution times out."""
        ...  # pragma: no cover


## Websockets ##
class _WSRequestContext(TypedDict):
    routeKey: str
    eventType: str
    extendedRequestId: str
    requestTime: str
    messageDirection: str
    stage: str
    connectedAt: int
    requestTimeEpoch: int
    identity: dict
    requestId: str
    domainName: str
    connectionId: str
    apiId: str


class WsEvent(TypedDict, total=False):
    headers: dict
    multiValueHeaders: dict
    requestContext: _WSRequestContext
    body: str
    isBase64Encoded: bool


## Tasks ##
class TaskEvent(TypedDict):
    schedule_type: Literal["RateSchedule", "CronSchedule"]
    schedule_name: str


## S3 ##
class _StorageUserIdentity(TypedDict):
    principalId: str


class _StorageRequestParameters(TypedDict):
    sourceIPAddress: str


class _StorageResponseElements(TypedDict):
    x_amz_request_id: str
    x_amz_id_2: str


class _StorageOwnerIdentity(TypedDict):
    principalId: str


class _StorageBucket(TypedDict):
    name: str
    ownerIdentity: _StorageOwnerIdentity
    arn: str


class _StorageObject(TypedDict):
    key: str
    size: int
    eTag: str
    sequencer: str


class _StorageS3(TypedDict):
    s3SchemaVersion: str
    configurationId: str
    bucket: _StorageBucket
    object: _StorageObject


class _StorageRecord(TypedDict):
    eventVersion: str
    eventSource: str
    awsRegion: str
    eventTime: str
    eventName: str
    userIdentity: _StorageUserIdentity
    requestParameters: _StorageRequestParameters
    responseElements: _StorageResponseElements
    s3: _StorageS3


class StorageEvent(TypedDict):
    Records: List[_StorageRecord]
