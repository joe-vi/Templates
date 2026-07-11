from enum import StrEnum


class CreateResult(StrEnum):
    """Outcome of any create/add operation, shared by all entities."""

    SUCCESS = "success"
    FAILURE = "failure"
    CONCURRENCY_ERROR = "concurrency_error"
    UNIQUE_CONSTRAINT_ERROR = "unique_constraint_error"


class UpdateResult(StrEnum):
    """Outcome of any update operation, shared by all entities."""

    SUCCESS = "success"
    FAILURE = "failure"
    CONCURRENCY_ERROR = "concurrency_error"
    UNIQUE_CONSTRAINT_ERROR = "unique_constraint_error"
    NOT_FOUND = "not_found"


class DeleteResult(StrEnum):
    """Outcome of any delete operation, shared by all entities."""

    SUCCESS = "success"
    FAILURE = "failure"
    CONCURRENCY_ERROR = "concurrency_error"
    NOT_FOUND = "not_found"


class LoginResult(StrEnum):
    """Outcome of a login or token refresh operation."""

    SUCCESS = "success"
    FAILURE = "failure"
    INVALID_CREDENTIALS = "invalid_credentials"
    USER_INACTIVE = "user_inactive"
