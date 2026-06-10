"""Conversion between auth API schemas and application DTOs."""

from src.api.routers.auth import auth_schema
from src.application.use_cases.auth import auth_dto


def to_login_dto(request: auth_schema.LoginRequest) -> auth_dto.LoginDTO:
    """Convert a login request to an application DTO.

    Args:
        request: The API request containing the login credentials.

    Returns:
        A LoginDTO populated with the username and password.
    """
    return auth_dto.LoginDTO(
        username=request.username, password=request.password
    )


def to_token_response(
    token_dto: auth_dto.TokenDTO,
) -> auth_schema.TokenResponse:
    """Convert a token DTO to an API response model.

    Args:
        token_dto: The application DTO containing the issued token pair.

    Returns:
        A TokenResponse populated with the token pair and token type.
    """
    return auth_schema.TokenResponse(
        access_token=token_dto.access_token,
        refresh_token=token_dto.refresh_token,
        token_type=token_dto.token_type,
    )
