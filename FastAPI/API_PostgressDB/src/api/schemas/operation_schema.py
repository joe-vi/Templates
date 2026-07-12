from pydantic import Field

from src.application.dto_base import DTOBase
from src.domain.enums import operation_results


class CreateOperationResponse(DTOBase):
    """Standard API response for any create operation."""

    result: operation_results.CreateResult
    message: str = Field(description="Human-readable description of the operation outcome")
    id: int | None = Field(default=None, description="Newly created entity id; None when operation failed")


class UpdateOperationResponse(DTOBase):
    """Standard API response for any update operation."""

    result: operation_results.UpdateResult
    message: str = Field(description="Human-readable description of the operation outcome")


class DeleteOperationResponse(DTOBase):
    """Standard API response for any delete operation."""

    result: operation_results.DeleteResult
    message: str = Field(description="Human-readable description of the operation outcome")
