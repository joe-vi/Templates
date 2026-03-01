"""Operation result enumerations for CRUD and auth operations."""

from enum import StrEnum


class CreateResult(StrEnum):
    """Represents the outcome of any create/add operation."""

    SUCCESS = "success"
    FAILURE = "failure"
    CONCURRENCY_ERROR = "concurrency_error"
    UNIQUE_CONSTRAINT_ERROR = "unique_constraint_error"


class UpdateResult(StrEnum):
    """Represents the outcome of any update operation."""

    SUCCESS = "success"
    FAILURE = "failure"
    CONCURRENCY_ERROR = "concurrency_error"
    UNIQUE_CONSTRAINT_ERROR = "unique_constraint_error"
    NOT_FOUND = "not_found"


class DeleteResult(StrEnum):
    """Represents the outcome of any delete operation."""

    SUCCESS = "success"
    FAILURE = "failure"
    CONCURRENCY_ERROR = "concurrency_error"
    NOT_FOUND = "not_found"


class LoginResult(StrEnum):
    """Represents the outcome of a login or token refresh operation."""

    SUCCESS = "success"
    FAILURE = "failure"
    INVALID_CREDENTIALS = "invalid_credentials"
    USER_INACTIVE = "user_inactive"
