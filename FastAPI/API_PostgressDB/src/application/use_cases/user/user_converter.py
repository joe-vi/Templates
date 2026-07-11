from src.application.use_cases.user import user_dto
from src.domain.entities.user.user import User


def to_dto(user: User) -> user_dto.UserDTO:
    """Convert a persisted domain user entity to a DTO.

    Args:
        user: The domain entity to convert; must be persisted (id and
            created_at populated).

    Returns:
        A UserDTO populated with the entity's data.

    Raises:
        ValueError: If the entity has not been persisted.
    """
    if user.id is None or user.created_at is None:
        raise ValueError("Cannot convert an unpersisted User to a UserDTO")

    return user_dto.UserDTO(
        id=user.id, email=user.email, username=user.username, role=user.role, status=user.status, created_at=user.created_at
    )


def to_dto_list(users: list[User]) -> list[user_dto.UserDTO]:
    """Convert a list of persisted domain user entities to DTOs.

    Args:
        users: The domain entities to convert.

    Returns:
        A list of UserDTOs, in the same order.
    """
    return [to_dto(user) for user in users]


def to_entity(create_user_dto: user_dto.CreateUserDTO, hashed_password: str) -> User:
    """Build an unpersisted domain user entity from a creation DTO.

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
