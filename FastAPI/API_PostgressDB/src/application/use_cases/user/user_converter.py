"""Conversion between user domain entities and application DTOs.

Module-level functions, not a class of static methods: in Python the module is
the namespace, so a never-instantiated class adds indirection without value.
"""

from src.application.use_cases.user import user_dto
from src.domain.entities.user.user import User


def to_dto(user: User) -> user_dto.UserDTO:
    """Convert a domain user entity to a DTO.

    Args:
        user: The domain entity to convert. Must be persisted (id and
            created_at populated).

    Returns:
        A UserDTO populated with the entity's data.
    """
    if user.id is None or user.created_at is None:
        raise ValueError("Cannot convert an unpersisted User to a UserDTO")

    return user_dto.UserDTO(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
    )


def to_dto_list(users: list[User]) -> list[user_dto.UserDTO]:
    """Convert a list of domain user entities to a list of DTOs.

    Args:
        users: The list of domain entities to convert.

    Returns:
        A list of UserDTOs.
    """
    return [to_dto(user) for user in users]


def to_entity(
    create_user_dto: user_dto.CreateUserDTO, hashed_password: str
) -> User:
    """Convert a creation DTO to a domain user entity.

    Args:
        create_user_dto: The DTO containing data for the new user.
        hashed_password: The hashed password to store on the entity.

    Returns:
        A new User entity with id set to None.
    """
    return User(
        id=None,
        email=create_user_dto.email,
        username=create_user_dto.username,
        hashed_password=hashed_password,
        role=create_user_dto.role,
        status=create_user_dto.status,
    )
