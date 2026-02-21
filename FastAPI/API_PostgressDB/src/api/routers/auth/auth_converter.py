from src.api.routers.auth.auth_schema import LoginRequest, TokenResponse
from src.application.use_cases.auth.auth_dto import LoginDTO, TokenDTO


class AuthConverter:
    """Converts between auth API request/response models and application DTOs."""

    @staticmethod
    def to_login_dto(request: LoginRequest) -> LoginDTO:
        """Convert a login request to a DTO for the application layer.

        Args:
            request: The API request containing the login credentials.

        Returns:
            A LoginDTO populated with the username and password.
        """
        return LoginDTO(username=request.username, password=request.password)

    @staticmethod
    def to_token_response(token_dto: TokenDTO) -> TokenResponse:
        """Convert a token DTO to an API response model.

        Args:
            token_dto: The application DTO containing the issued token pair.

        Returns:
            A TokenResponse populated with the access token, refresh token, and token type.
        """
        return TokenResponse(
            access_token=token_dto.access_token,
            refresh_token=token_dto.refresh_token,
            token_type=token_dto.token_type,
        )
