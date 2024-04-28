class NoHandlerFound(Exception):
    """
    Exception raised when no handler is found for the event
    """


class MissingStackResource(Exception):
    """
    Exception raised when a stack resource is missing
    """


class FailedToSyncProject(Exception):
    """
    Exception raised when a project fails to sync
    """
