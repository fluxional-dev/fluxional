class FailedImageBuild(Exception):
    """
    Exception raised when the docker image fails to build
    """


class FailedContainerBuild(Exception):
    """
    Exception raised when the docker container fails to build
    """


class FailedToRunContainer(Exception):
    """
    Exception raised when the docker container fails to run
    """
