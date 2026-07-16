from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ContractModel(BaseModel):
    """Neutral base for objects crossing the API boundary: camelCase JSON on the wire, accepts either case in, frozen."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, frozen=True)
