from src.api.routers.user.user_schema import UserCreateRequest, UserResponse, UserUpdateRoleRequest
from src.application.use_cases.user.user_dto import CreateUserDTO, UpdateUserRoleDTO, UserDTO


class UserConverter:
    """Converts between API request/response models and application DTOs."""

    @staticmethod
    def to_create_dto(request: UserCreateRequest) -> CreateUserDTO:
        """Convert a create user request to a DTO for the application layer.

        Args:
            request: The API request containing the user creation data.

        Returns:
            A CreateUserDTO populated with data from the request.
        """
        return CreateUserDTO(
            email=request.email,
            username=request.username,
            password=request.password,
            role=request.role,
            status=request.status,
        )

    @staticmethod
    def to_update_role_dto(user_id: int, request: UserUpdateRoleRequest) -> UpdateUserRoleDTO:
        """Convert an update role request to a DTO for the application layer.

        Args:
            user_id: The unique identifier of the user whose role is being updated.
            request: The API request containing the new role.

        Returns:
            An UpdateUserRoleDTO populated with the user id and new role.
        """
        return UpdateUserRoleDTO(user_id=user_id, role=request.role)

    @staticmethod
    def to_response(user_dto: UserDTO) -> UserResponse:
        """Convert a user DTO to an API response model.

        Args:
            user_dto: The application DTO containing user data.

        Returns:
            A UserResponse populated with data from the DTO.
        """
        return UserResponse(
            id=user_dto.id,
            email=user_dto.email,
            username=user_dto.username,
            role=user_dto.role,
            status=user_dto.status,
            created_at=user_dto.created_at,
        )

    @staticmethod
    def to_response_list(user_dtos: list[UserDTO]) -> list[UserResponse]:
        """Convert a list of user DTOs to a list of API response models.

        Args:
            user_dtos: The list of application DTOs to convert.

        Returns:
            A list of UserResponse models, one per DTO.
        """
        return [UserConverter.to_response(user_dto) for user_dto in user_dtos]
