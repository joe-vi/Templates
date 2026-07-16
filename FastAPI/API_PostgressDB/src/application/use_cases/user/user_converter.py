from src.application.use_cases.user import user_contracts
from src.domain.entities.user.user import User


def to_response(user: User) -> user_contracts.UserResponse:
    """Convert a persisted domain user entity to a response model.

    Args:
        user: The domain entity to convert; must be persisted (id and
            created_at populated).

    Returns:
        A UserResponse populated with the entity's data.

    Raises:
        ValueError: If the entity has not been persisted.
    """
    if user.id is None or user.created_at is None:
        raise ValueError("Cannot convert an unpersisted User to a UserResponse")

    return user_contracts.UserResponse(
        id=user.id, email=user.email, username=user.username, role=user.role, status=user.status, created_at=user.created_at
    )


def to_response_list(users: list[User]) -> list[user_contracts.UserResponse]:
    """Convert a list of persisted domain user entities to response models.

    Args:
        users: The domain entities to convert.

    Returns:
        A list of UserResponses, in the same order.
    """
    return [to_response(user) for user in users]


def to_entity(create_user_request: user_contracts.CreateUserRequest, hashed_password: str) -> User:
    """Build an unpersisted domain user entity from a creation request.

    Args:
        create_user_request: The request data for the new user.
        hashed_password: The hashed password to store on the entity.

    Returns:
        A new User entity with id set to None.
    """
    return User(
        id=None,
        email=create_user_request.email,
        username=create_user_request.username,
        hashed_password=hashed_password,
        role=create_user_request.role,
        status=create_user_request.status,
    )
