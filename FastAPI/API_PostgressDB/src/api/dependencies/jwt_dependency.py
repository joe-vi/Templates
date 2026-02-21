from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_injector import Injected

from src.application.services.token_service_base import TokenServiceBase
from src.application.services.user_context_base import UserContextBase
from src.application.use_cases.auth.auth_dto import TokenClaimsDTO

_security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    token_service: TokenServiceBase = Injected(TokenServiceBase),
    user_context: UserContextBase = Injected(UserContextBase),
) -> TokenClaimsDTO:
    """FastAPI dependency that validates the Bearer JWT access token.

    Decodes the token, raises 401 on any failure, then populates the
    request-scoped UserContextBase so that any injected component (use case,
    service, etc.) can read the current user's identity without needing the
    token passed through function signatures.

    Args:
        credentials: The HTTP Bearer credentials from the Authorization header.
        token_service: The injected token service used to decode and verify the JWT.
        user_context: The request-scoped context populated with the decoded claims.

    Returns:
        A TokenClaimsDTO containing the authenticated user's id, username, and role.

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

    user_context.populate(token_claims.user_id, token_claims.username, token_claims.role)

    return token_claims
