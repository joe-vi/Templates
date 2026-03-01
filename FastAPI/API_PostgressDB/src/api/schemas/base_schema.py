"""Base Pydantic model providing camelCase serialisation for all API schemas."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class APIModelBase(BaseModel):
    """Base Pydantic model for all API schemas.

    Python attribute names remain snake_case; JSON uses camelCase.
    Both forms are accepted on input (populate_by_name=True).
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
