from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.dependencies.injected import Injected
from src.application.services.token_service import TokenService
from src.application.services.user_context import UserContext
from src.application.use_cases.auth import auth_dto
from src.infrastructure.logging import log_context

_security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_security)],
    token_service: Annotated[TokenService, Injected(TokenService)],
    user_context: Annotated[UserContext, Injected(UserContext)],
) -> auth_dto.TokenClaimsDTO:
    """Validate the Bearer JWT access token and return its claims.

    Decodes the token, raising 401 on any failure, then populates the
    request-scoped ``UserContext`` (so any injected use case or service can
    read the caller's identity) and records the user id in the logging
    context so it appears on every log line for the rest of the request.
    Route handlers can also receive the returned ``TokenClaimsDTO`` directly
    via ``Depends(get_current_user)``.

    Args:
        credentials: The HTTP Bearer credentials from the Authorization header.
        token_service: The token service used to decode the JWT.
        user_context: The request-scoped identity holder to populate.

    Returns:
        A TokenClaimsDTO containing the authenticated user's id and role.

    Raises:
        HTTPException: 401 Unauthorized if the token is invalid or expired.
    """
    token_claims = token_service.decode_access_token(credentials.credentials)

    if token_claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"}
        )

    user_context.populate(token_claims.user_id, token_claims.role)
    log_context.user_id_var.set(token_claims.user_id)

    return token_claims
