from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DTOBase(BaseModel):
    """Base Pydantic model for every DTO and response envelope."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, frozen=True)
