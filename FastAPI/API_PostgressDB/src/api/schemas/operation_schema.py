from pydantic import Field

from src.api.schemas.base_schema import CamelCaseModel
from src.domain.enums.operation_results import CreateResult, DeleteResult, UpdateResult


class CreateOperationResponse(CamelCaseModel):
    """Standard API response for any create operation.

    Reusable across all entities — import and return this from any POST endpoint.
    The id field carries the newly created entity id on success and is None otherwise.
    """

    result: CreateResult
    message: str = Field(description="Human-readable description of the operation outcome")
    id: int | None = Field(default=None, description="Newly created entity id; None when the operation did not succeed")


class UpdateOperationResponse(CamelCaseModel):
    """Standard API response for any update operation.

    Reusable across all entities — import and return this from any PUT/PATCH endpoint.
    """

    result: UpdateResult
    message: str = Field(description="Human-readable description of the operation outcome")


class DeleteOperationResponse(CamelCaseModel):
    """Standard API response for any delete operation.

    Reusable across all entities — import and return this from any DELETE endpoint.
    """

    result: DeleteResult
    message: str = Field(description="Human-readable description of the operation outcome")
