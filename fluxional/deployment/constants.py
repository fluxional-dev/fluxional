# Required mounted volumes to run docker inside docker
DID_VOLUME = {"/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"}}
# Base image used to run docker inside docker
BASE_IMAGE = "fluxionality/cdk_deploy:latest"
# Base workdir
BASE_WORKDIR = "/app"
# CDK DEPLOYMENT COMMAND
CDK_DEPLOY_CMD = "cdk deploy --app 'python3 {app} --synth' --require-approval never"
CDK_DESTROY_CMD = "cdk destroy --app 'python3 {app} --synth' --force"
# AWS LAMBDA BASE IMAGE
AWS_LAMBDA_PYTHON_3_10_IMAGE = "public.ecr.aws/lambda/python:3.10"
AWS_LAMBDA_PYTHON_3_11_IMAGE = "public.ecr.aws/lambda/python:3.11"
AWS_LAMBDA_PYTHON_3_12_IMAGE = "public.ecr.aws/lambda/python:3.12"
RUNTIMES = {
    "3.10": AWS_LAMBDA_PYTHON_3_10_IMAGE,
    "3.11": AWS_LAMBDA_PYTHON_3_11_IMAGE,
    "3.12": AWS_LAMBDA_PYTHON_3_12_IMAGE,
}

# OTEL
OTEL_WRAPPER_FILE = "https://tjaws.s3.amazonaws.com/otel_wrapper.py"
OTEL_INST_FILE = "https://tjaws.s3.amazonaws.com/otel-instrument"
OTEL_REQ_FILE = "https://tjaws.s3.amazonaws.com/requirements_otel.txt"

# Fluxional Telemetry Extensions
FTE_EXTENSION = (
    "https://tjaws.s3.amazonaws.com/python-example-telemetry-api-extension.zip"
)
