from pydantic import Field

from src.domain.enums import operation_results
from src.shared.contract_model import ContractModel


class CreateOperationResponse(ContractModel):
    """Standard API response for any create operation."""

    result: operation_results.CreateResult
    message: str = Field(description="Human-readable description of the operation outcome")
    id: int | None = Field(default=None, description="Newly created entity id; None when operation failed")


class UpdateOperationResponse(ContractModel):
    """Standard API response for any update operation."""

    result: operation_results.UpdateResult
    message: str = Field(description="Human-readable description of the operation outcome")


class DeleteOperationResponse(ContractModel):
    """Standard API response for any delete operation."""

    result: operation_results.DeleteResult
    message: str = Field(description="Human-readable description of the operation outcome")
