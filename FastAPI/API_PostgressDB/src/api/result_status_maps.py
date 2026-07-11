from fastapi import status

from src.domain.enums import operation_results

CREATE_STATUS_MAP: dict[operation_results.CreateResult, int] = {
    operation_results.CreateResult.SUCCESS: status.HTTP_201_CREATED,
    operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR: status.HTTP_409_CONFLICT,
    operation_results.CreateResult.CONCURRENCY_ERROR: status.HTTP_409_CONFLICT,
    operation_results.CreateResult.FAILURE: status.HTTP_500_INTERNAL_SERVER_ERROR,
}

CREATE_MESSAGE_MAP: dict[operation_results.CreateResult, str] = {
    operation_results.CreateResult.SUCCESS: "Created successfully",
    operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR: "Conflict: resource already exists",
    operation_results.CreateResult.CONCURRENCY_ERROR: "Conflict: concurrent modification detected",
    operation_results.CreateResult.FAILURE: "Operation failed",
}

UPDATE_STATUS_MAP: dict[operation_results.UpdateResult, int] = {
    operation_results.UpdateResult.SUCCESS: status.HTTP_200_OK,
    operation_results.UpdateResult.UNIQUE_CONSTRAINT_ERROR: status.HTTP_409_CONFLICT,
    operation_results.UpdateResult.CONCURRENCY_ERROR: status.HTTP_409_CONFLICT,
    operation_results.UpdateResult.FAILURE: status.HTTP_500_INTERNAL_SERVER_ERROR,
    operation_results.UpdateResult.NOT_FOUND: status.HTTP_404_NOT_FOUND,
}

UPDATE_MESSAGE_MAP: dict[operation_results.UpdateResult, str] = {
    operation_results.UpdateResult.SUCCESS: "Updated successfully",
    operation_results.UpdateResult.UNIQUE_CONSTRAINT_ERROR: "Conflict: resource already exists",
    operation_results.UpdateResult.CONCURRENCY_ERROR: "Conflict: concurrent modification detected",
    operation_results.UpdateResult.FAILURE: "Operation failed",
    operation_results.UpdateResult.NOT_FOUND: "Resource not found",
}

DELETE_STATUS_MAP: dict[operation_results.DeleteResult, int] = {
    operation_results.DeleteResult.SUCCESS: status.HTTP_200_OK,
    operation_results.DeleteResult.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    operation_results.DeleteResult.CONCURRENCY_ERROR: status.HTTP_409_CONFLICT,
    operation_results.DeleteResult.FAILURE: status.HTTP_500_INTERNAL_SERVER_ERROR,
}

DELETE_MESSAGE_MAP: dict[operation_results.DeleteResult, str] = {
    operation_results.DeleteResult.SUCCESS: "Deleted successfully",
    operation_results.DeleteResult.NOT_FOUND: "Resource not found",
    operation_results.DeleteResult.CONCURRENCY_ERROR: "Conflict: concurrent modification detected",
    operation_results.DeleteResult.FAILURE: "Operation failed",
}
