"""Shared base for all DTOs.

DTOs are the single model set for both the application layer and the API
boundary: routes accept and return them directly (no separate request or
response schemas), so validation rules live here too.

Python code always uses snake_case attribute names. On the wire, JSON uses
camelCase: the alias generator drives both FastAPI's response serialisation
(``by_alias=True``) and the OpenAPI schema, and ``populate_by_name=True``
accepts either case on input — including plain keyword construction in
use cases and tests. Instances are frozen, like the dataclass DTOs they
replace.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DTOBase(BaseModel):
    """Base Pydantic model for all DTOs (camelCase JSON, frozen)."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        frozen=True,
    )
