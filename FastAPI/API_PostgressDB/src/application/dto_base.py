from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DTOBase(BaseModel):
    """Base Pydantic model for every DTO and response envelope.

    DTOs are the single model set for both the application layer and the API
    boundary: routes accept and return them directly (no separate request or
    response schemas), so field validation rules live on the DTOs.

    Python code always uses snake_case attribute names. On the wire, JSON uses
    camelCase: the alias generator drives both FastAPI's response
    serialisation and the OpenAPI schema, and ``populate_by_name=True``
    accepts either case on input — including plain keyword construction in
    use cases and tests. Instances are frozen.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, frozen=True)
