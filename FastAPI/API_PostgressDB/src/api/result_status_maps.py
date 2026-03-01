"""Shared helpers mapping operation result enums to HTTP responses."""

from fastapi import status
from fastapi.responses import JSONResponse

from src.api.schemas import operation_schema
from src.domain.enums import operation_results

CREATE_STATUS_MAP: dict[operation_results.CreateResult, int] = {
    operation_results.CreateResult.SUCCESS: status.HTTP_201_CREATED,
    operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR: status.HTTP_409_CONFLICT,  # noqa: E501
    operation_results.CreateResult.CONCURRENCY_ERROR: status.HTTP_409_CONFLICT,
    operation_results.CreateResult.FAILURE: status.HTTP_500_INTERNAL_SERVER_ERROR,  # noqa: E501
}

CREATE_MESSAGE_MAP: dict[operation_results.CreateResult, str] = {
    operation_results.CreateResult.SUCCESS: "Created successfully",
    operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR: "Conflict: resource already exists",  # noqa: E501
    operation_results.CreateResult.CONCURRENCY_ERROR: "Conflict: concurrent modification detected",  # noqa: E501
    operation_results.CreateResult.FAILURE: "Operation failed",
}

UPDATE_STATUS_MAP: dict[operation_results.UpdateResult, int] = {
    operation_results.UpdateResult.SUCCESS: status.HTTP_200_OK,
    operation_results.UpdateResult.UNIQUE_CONSTRAINT_ERROR: status.HTTP_409_CONFLICT,  # noqa: E501
    operation_results.UpdateResult.CONCURRENCY_ERROR: status.HTTP_409_CONFLICT,
    operation_results.UpdateResult.FAILURE: status.HTTP_500_INTERNAL_SERVER_ERROR,  # noqa: E501
    operation_results.UpdateResult.NOT_FOUND: status.HTTP_404_NOT_FOUND,
}

UPDATE_MESSAGE_MAP: dict[operation_results.UpdateResult, str] = {
    operation_results.UpdateResult.SUCCESS: "Updated successfully",
    operation_results.UpdateResult.UNIQUE_CONSTRAINT_ERROR: "Conflict: resource already exists",  # noqa: E501
    operation_results.UpdateResult.CONCURRENCY_ERROR: "Conflict: concurrent modification detected",  # noqa: E501
    operation_results.UpdateResult.FAILURE: "Operation failed",
    operation_results.UpdateResult.NOT_FOUND: "Resource not found",
}

DELETE_STATUS_MAP: dict[operation_results.DeleteResult, int] = {
    operation_results.DeleteResult.SUCCESS: status.HTTP_200_OK,
    operation_results.DeleteResult.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    operation_results.DeleteResult.CONCURRENCY_ERROR: status.HTTP_409_CONFLICT,
    operation_results.DeleteResult.FAILURE: status.HTTP_500_INTERNAL_SERVER_ERROR,  # noqa: E501
}

DELETE_MESSAGE_MAP: dict[operation_results.DeleteResult, str] = {
    operation_results.DeleteResult.SUCCESS: "Deleted successfully",
    operation_results.DeleteResult.NOT_FOUND: "Resource not found",
    operation_results.DeleteResult.CONCURRENCY_ERROR: "Conflict: concurrent modification detected",  # noqa: E501
    operation_results.DeleteResult.FAILURE: "Operation failed",
}


def create_response(
    result: operation_results.CreateResult, entity_id: int | None
) -> JSONResponse:
    """Build a JSONResponse for a create operation result.

    Args:
        result: The CreateResult enum value from the use case.
        entity_id: The newly created entity id; None when the operation failed.

    Returns:
        A JSONResponse with a CreateOperationResponse body and the
        corresponding HTTP status code.
    """
    return JSONResponse(
        content=operation_schema.CreateOperationResponse(
            result=result, message=CREATE_MESSAGE_MAP[result], id=entity_id
        ).model_dump(),
        status_code=CREATE_STATUS_MAP[result],
    )


def update_response(result: operation_results.UpdateResult) -> JSONResponse:
    """Build a JSONResponse for an update operation result.

    Args:
        result: The UpdateResult enum value from the use case.

    Returns:
        A JSONResponse with an UpdateOperationResponse body and the
        corresponding HTTP status code.
    """
    return JSONResponse(
        content=operation_schema.UpdateOperationResponse(
            result=result, message=UPDATE_MESSAGE_MAP[result]
        ).model_dump(),
        status_code=UPDATE_STATUS_MAP[result],
    )


def delete_response(result: operation_results.DeleteResult) -> JSONResponse:
    """Build a JSONResponse for a delete operation result.

    Args:
        result: The DeleteResult enum value from the use case.

    Returns:
        A JSONResponse with a DeleteOperationResponse body and the
        corresponding HTTP status code.
    """
    return JSONResponse(
        content=operation_schema.DeleteOperationResponse(
            result=result, message=DELETE_MESSAGE_MAP[result]
        ).model_dump(),
        status_code=DELETE_STATUS_MAP[result],
    )
