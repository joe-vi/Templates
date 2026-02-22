from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class APIModelBase(BaseModel):
    """Base Pydantic model for all API schemas.

    Python attribute names remain snake_case; the JSON representation uses camelCase.
    Both snake_case and camelCase are accepted on input (populate_by_name=True).
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
