"""FastAPI dependency for JWT Bearer token validation."""

from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.services.token_service import TokenService
from src.application.use_cases.auth import auth_dto
from src.infrastructure.logging import log_context

_security = HTTPBearer()


@inject
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_security)],
    token_service: FromDishka[TokenService],
) -> auth_dto.TokenClaimsDTO:
    """Validate the Bearer JWT access token and return its claims.

    Decodes the token, raising 401 on any failure, and records the
    authenticated user id in the logging context so it appears on every log
    line for the rest of the request. Components needing the caller's identity
    depend on this function and receive the returned ``TokenClaimsDTO``.

    Args:
        credentials: The HTTP Bearer credentials from the Authorization header.
        token_service: The token service used to decode the JWT.

    Returns:
        A TokenClaimsDTO containing the authenticated user's id and role.

    Raises:
        HTTPException: 401 Unauthorized if the token is invalid or expired.
    """
    token_claims = token_service.decode_access_token(credentials.credentials)

    if token_claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    log_context.user_id_var.set(token_claims.user_id)

    return token_claims
