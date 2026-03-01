"""Converter between user domain entities and application DTOs."""

from src.application.use_cases.user import user_dto as user_dto_module
from src.domain.entities.user import user as user_module


class UserEntityConverter:
    """Converts between domain entities and DTOs."""

    @staticmethod
    def to_dto(user: user_module.User) -> user_dto_module.UserDTO:
        """Convert a domain user entity to a DTO.

        Args:
            user: The domain entity to convert.

        Returns:
            A UserDTO populated with the entity's data.
        """
        return user_dto_module.UserDTO(
            id=user.id,  # type: ignore
            email=user.email,
            username=user.username,
            role=user.role,
            status=user.status,
            created_at=user.created_at,  # type: ignore
        )

    @staticmethod
    def to_dto_list(
        users: list[user_module.User],
    ) -> list[user_dto_module.UserDTO]:
        """Convert a list of domain user entities to a list of DTOs.

        Args:
            users: The list of domain entities to convert.

        Returns:
            A list of UserDTOs.
        """
        return [UserEntityConverter.to_dto(user) for user in users]

    @staticmethod
    def to_entity(
        create_user_dto: user_dto_module.CreateUserDTO, hashed_password: str
    ) -> user_module.User:
        """Convert a creation DTO to a domain user entity.

        Args:
            create_user_dto: The DTO containing data for the new user.
            hashed_password: The bcrypt-hashed password to store on the entity.

        Returns:
            A new User entity with id set to None.
        """
        return user_module.User(
            id=None,
            email=create_user_dto.email,
            username=create_user_dto.username,
            hashed_password=hashed_password,
            role=create_user_dto.role,
            status=create_user_dto.status,
        )
