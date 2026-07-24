from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.dependencies.injected import Injected
from src.ports.token_service import TokenClaims, TokenService
from src.ports.user_context import UserContext

_security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_security)],
    token_service: Injected[TokenService],
    user_context: Injected[UserContext],
) -> TokenClaims:
    """Validate the Bearer JWT access token and return its claims.

    Args:
        credentials: The HTTP Bearer credentials from the Authorization header.
        token_service: The token service used to decode the JWT.
        user_context: The request-scoped identity holder to populate.

    Returns:
        The TokenClaims containing the authenticated user's id and role.

    Raises:
        HTTPException: 401 Unauthorized if the token is invalid or expired.
    """
    token_claims = token_service.decode_access_token(credentials.credentials)

    if token_claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"}
        )

    user_context.populate(token_claims.user_id, token_claims.role)

    return token_claims
