"""PyJWT implementation of the token service."""

from datetime import UTC, datetime, timedelta

import jwt
from injector import inject
from jwt.exceptions import InvalidTokenError

from src.application.services import token_service_base
from src.application.use_cases.auth import auth_dto
from src.config import settings as settings_module
from src.domain.enums import user_enum

_ACCESS_TOKEN_TYPE = "access"
_REFRESH_TOKEN_TYPE = "refresh"


class TokenService(token_service_base.TokenServiceBase):
    """PyJWT implementation of TokenServiceBase using HS256.

    To switch providers or algorithms, create a new class that implements
    TokenServiceBase and update the binding in container.py.
    """

    @inject
    def __init__(self, settings: settings_module.Settings) -> None:
        """Initialize the token service with JWT configuration.

        Args:
            settings: Application settings containing secret key, algorithm,
                and expiry values.
        """
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_expire_minutes = settings.access_token_expire_minutes
        self._refresh_expire_days = settings.refresh_token_expire_days

    def create_access_token(self, user_id: int, role: str) -> str:
        expire = datetime.now(UTC) + timedelta(
            minutes=self._access_expire_minutes
        )
        payload = {
            "sub": str(user_id),
            "role": role,
            "type": _ACCESS_TOKEN_TYPE,
            "exp": expire,
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_refresh_token(self, user_id: int, role: str) -> str:
        expire = datetime.now(UTC) + timedelta(days=self._refresh_expire_days)
        payload = {
            "sub": str(user_id),
            "role": role,
            "type": _REFRESH_TOKEN_TYPE,
            "exp": expire,
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> auth_dto.TokenClaimsDTO | None:
        return self._decode_token(token, _ACCESS_TOKEN_TYPE)

    def decode_refresh_token(
        self, token: str
    ) -> auth_dto.TokenClaimsDTO | None:
        return self._decode_token(token, _REFRESH_TOKEN_TYPE)

    def _decode_token(
        self, token: str, expected_type: str
    ) -> auth_dto.TokenClaimsDTO | None:
        try:
            payload = jwt.decode(
                token, self._secret_key, algorithms=[self._algorithm]
            )
            if payload.get("type") != expected_type:
                return None
            return auth_dto.TokenClaimsDTO(
                user_id=int(payload["sub"]),
                role=user_enum.UserRole(payload["role"]),
            )
        except (InvalidTokenError, KeyError, ValueError):
            return None
