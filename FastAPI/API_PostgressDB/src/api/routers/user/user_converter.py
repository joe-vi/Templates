"""Conversion between user API schemas and application DTOs."""

from src.api.routers.user import user_schema
from src.application.use_cases.user import user_dto


def to_create_dto(
    request: user_schema.UserCreateRequest,
) -> user_dto.CreateUserDTO:
    """Convert a create-user request to an application DTO.

    Args:
        request: The API request containing the user creation data.

    Returns:
        A CreateUserDTO populated with data from the request.
    """
    return user_dto.CreateUserDTO(
        email=request.email,
        username=request.username,
        password=request.password,
        role=request.role,
        status=request.status,
    )


def to_update_role_dto(
    user_id: int, request: user_schema.UserUpdateRoleRequest
) -> user_dto.UpdateUserRoleDTO:
    """Convert an update-role request to an application DTO.

    Args:
        user_id: The unique identifier of the user whose role is updated.
        request: The API request containing the new role.

    Returns:
        An UpdateUserRoleDTO populated with the user id and new role.
    """
    return user_dto.UpdateUserRoleDTO(user_id=user_id, role=request.role)


def to_response(dto: user_dto.UserDTO) -> user_schema.UserResponse:
    """Convert a user DTO to an API response model.

    Args:
        dto: The application DTO containing user data.

    Returns:
        A UserResponse populated with data from the DTO.
    """
    return user_schema.UserResponse(
        id=dto.id,
        email=dto.email,
        username=dto.username,
        role=dto.role,
        status=dto.status,
        created_at=dto.created_at,
    )


def to_response_list(
    dtos: list[user_dto.UserDTO],
) -> list[user_schema.UserResponse]:
    """Convert a list of user DTOs to API response models.

    Args:
        dtos: The list of application DTOs to convert.

    Returns:
        A list of UserResponse models, one per DTO.
    """
    return [to_response(dto) for dto in dtos]
