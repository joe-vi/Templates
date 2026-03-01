"""Converter between user API schemas and application DTOs."""

from src.api.routers.user import user_schema
from src.application.use_cases.user import user_dto as user_dto_module


class UserConverter:
    """Converts between API request/response models and application DTOs."""

    @staticmethod
    def to_create_dto(
        request: user_schema.UserCreateRequest,
    ) -> user_dto_module.CreateUserDTO:
        """Convert a create user request to a DTO for the application layer.

        Args:
            request: The API request containing the user creation data.

        Returns:
            A CreateUserDTO populated with data from the request.
        """
        return user_dto_module.CreateUserDTO(
            email=request.email,
            username=request.username,
            password=request.password,
            role=request.role,
            status=request.status,
        )

    @staticmethod
    def to_update_role_dto(
        user_id: int, request: user_schema.UserUpdateRoleRequest
    ) -> user_dto_module.UpdateUserRoleDTO:
        """Convert an update role request to a DTO for the application layer.

        Args:
            user_id: The unique identifier of the user whose role is updated.
            request: The API request containing the new role.

        Returns:
            An UpdateUserRoleDTO populated with the user id and new role.
        """
        return user_dto_module.UpdateUserRoleDTO(
            user_id=user_id, role=request.role
        )

    @staticmethod
    def to_response(
        user_dto: user_dto_module.UserDTO,
    ) -> user_schema.UserResponse:
        """Convert a user DTO to an API response model.

        Args:
            user_dto: The application DTO containing user data.

        Returns:
            A UserResponse populated with data from the DTO.
        """
        return user_schema.UserResponse(
            id=user_dto.id,
            email=user_dto.email,
            username=user_dto.username,
            role=user_dto.role,
            status=user_dto.status,
            created_at=user_dto.created_at,
        )

    @staticmethod
    def to_response_list(
        user_dtos: list[user_dto_module.UserDTO],
    ) -> list[user_schema.UserResponse]:
        """Convert a list of user DTOs to a list of API response models.

        Args:
            user_dtos: The list of application DTOs to convert.

        Returns:
            A list of UserResponse models, one per DTO.
        """
        return [UserConverter.to_response(user_dto) for user_dto in user_dtos]
