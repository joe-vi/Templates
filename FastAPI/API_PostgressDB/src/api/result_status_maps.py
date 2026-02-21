from fastapi import status
from fastapi.responses import JSONResponse

from src.api.schemas.operation_schema import CreateOperationResponse, DeleteOperationResponse, UpdateOperationResponse
from src.domain.enums.operation_results import CreateResult, DeleteResult, UpdateResult

CREATE_STATUS_MAP: dict[CreateResult, int] = {
    CreateResult.SUCCESS: status.HTTP_201_CREATED,
    CreateResult.UNIQUE_CONSTRAINT_ERROR: status.HTTP_409_CONFLICT,
    CreateResult.CONCURRENCY_ERROR: status.HTTP_409_CONFLICT,
    CreateResult.FAILURE: status.HTTP_500_INTERNAL_SERVER_ERROR,
}

CREATE_MESSAGE_MAP: dict[CreateResult, str] = {
    CreateResult.SUCCESS: "Created successfully",
    CreateResult.UNIQUE_CONSTRAINT_ERROR: "Conflict: resource already exists",
    CreateResult.CONCURRENCY_ERROR: "Conflict: concurrent modification detected",
    CreateResult.FAILURE: "Operation failed",
}

UPDATE_STATUS_MAP: dict[UpdateResult, int] = {
    UpdateResult.SUCCESS: status.HTTP_200_OK,
    UpdateResult.UNIQUE_CONSTRAINT_ERROR: status.HTTP_409_CONFLICT,
    UpdateResult.CONCURRENCY_ERROR: status.HTTP_409_CONFLICT,
    UpdateResult.FAILURE: status.HTTP_500_INTERNAL_SERVER_ERROR,
    UpdateResult.NOT_FOUND: status.HTTP_404_NOT_FOUND,
}

UPDATE_MESSAGE_MAP: dict[UpdateResult, str] = {
    UpdateResult.SUCCESS: "Updated successfully",
    UpdateResult.UNIQUE_CONSTRAINT_ERROR: "Conflict: resource already exists",
    UpdateResult.CONCURRENCY_ERROR: "Conflict: concurrent modification detected",
    UpdateResult.FAILURE: "Operation failed",
    UpdateResult.NOT_FOUND: "Resource not found",
}

DELETE_STATUS_MAP: dict[DeleteResult, int] = {
    DeleteResult.SUCCESS: status.HTTP_200_OK,
    DeleteResult.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    DeleteResult.CONCURRENCY_ERROR: status.HTTP_409_CONFLICT,
    DeleteResult.FAILURE: status.HTTP_500_INTERNAL_SERVER_ERROR,
}

DELETE_MESSAGE_MAP: dict[DeleteResult, str] = {
    DeleteResult.SUCCESS: "Deleted successfully",
    DeleteResult.NOT_FOUND: "Resource not found",
    DeleteResult.CONCURRENCY_ERROR: "Conflict: concurrent modification detected",
    DeleteResult.FAILURE: "Operation failed",
}


def create_response(result: CreateResult, entity_id: int | None) -> JSONResponse:
    return JSONResponse(
        content=CreateOperationResponse(result=result, message=CREATE_MESSAGE_MAP[result], id=entity_id).model_dump(),
        status_code=CREATE_STATUS_MAP[result],
    )


def update_response(result: UpdateResult) -> JSONResponse:
    return JSONResponse(
        content=UpdateOperationResponse(result=result, message=UPDATE_MESSAGE_MAP[result]).model_dump(),
        status_code=UPDATE_STATUS_MAP[result],
    )


def delete_response(result: DeleteResult) -> JSONResponse:
    return JSONResponse(
        content=DeleteOperationResponse(result=result, message=DELETE_MESSAGE_MAP[result]).model_dump(),
        status_code=DELETE_STATUS_MAP[result],
    )
