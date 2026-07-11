from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DTOBase(BaseModel):
    """Base Pydantic model for every DTO and response envelope.

    snake_case attribute names in Python; camelCase on the wire. Accepts
    either case on input. Instances are frozen.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, frozen=True)
