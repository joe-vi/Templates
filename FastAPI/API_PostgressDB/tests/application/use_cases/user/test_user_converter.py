from datetime import datetime

from src.application.use_cases.user.user_converter import UserEntityConverter
from src.application.use_cases.user.user_dto import CreateUserDTO, UserDTO
from src.domain.entities.user.user import User
from src.domain.enums.user_enum import UserRole, UserStatus


def _make_user(user_id: int = 1) -> User:
    return User(
        id=user_id,
        email="alice@example.com",
        username="alice",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


class TestToDto:
    def test_maps_all_fields_from_entity(self):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        user = User(
            id=1,
            email="alice@example.com",
            username="alice",
            role=UserRole.ADMIN,
            status=UserStatus.INACTIVE,
            created_at=created_at,
        )

        user_dto = UserEntityConverter.to_dto(user)

        assert isinstance(user_dto, UserDTO)
        assert user_dto.id == 1
        assert user_dto.email == "alice@example.com"
        assert user_dto.username == "alice"
        assert user_dto.role == UserRole.ADMIN
        assert user_dto.status == UserStatus.INACTIVE
        assert user_dto.created_at == created_at

    def test_preserves_user_role_enum(self):
        user = _make_user()
        user_dto = UserEntityConverter.to_dto(user)
        assert user_dto.role == UserRole.ADMIN

    def test_preserves_user_status_enum(self):
        user = User(
            id=1, email="bob@example.com", username="bob",
            role=UserRole.USER, status=UserStatus.INACTIVE,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )
        user_dto = UserEntityConverter.to_dto(user)
        assert user_dto.status == UserStatus.INACTIVE


class TestToDtoList:
    def test_maps_each_user_to_dto(self):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        users = [
            User(id=1, email="alice@example.com", username="alice", role=UserRole.ADMIN, status=UserStatus.ACTIVE, created_at=created_at),
            User(id=2, email="bob@example.com", username="bob", role=UserRole.USER, status=UserStatus.INACTIVE, created_at=created_at),
        ]

        user_dtos = UserEntityConverter.to_dto_list(users)

        assert len(user_dtos) == 2
        assert user_dtos[0].id == 1
        assert user_dtos[0].email == "alice@example.com"
        assert user_dtos[1].id == 2
        assert user_dtos[1].email == "bob@example.com"

    def test_returns_empty_list_when_given_no_users(self):
        user_dtos = UserEntityConverter.to_dto_list([])
        assert user_dtos == []

    def test_preserves_order_of_users(self):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        users = [
            User(id=id, email=f"user{id}@example.com", username=f"user{id}", role=UserRole.USER, status=UserStatus.ACTIVE, created_at=created_at)
            for id in [3, 1, 2]
        ]

        user_dtos = UserEntityConverter.to_dto_list(users)

        assert [dto.id for dto in user_dtos] == [3, 1, 2]


class TestToEntity:
    def test_sets_id_to_none(self):
        create_user_dto = CreateUserDTO(email="alice@example.com", username="alice")

        user = UserEntityConverter.to_entity(create_user_dto)

        assert user.id is None

    def test_maps_all_fields_from_dto(self):
        create_user_dto = CreateUserDTO(
            email="alice@example.com",
            username="alice",
            role=UserRole.ADMIN,
            status=UserStatus.INACTIVE,
        )

        user = UserEntityConverter.to_entity(create_user_dto)

        assert isinstance(user, User)
        assert user.email == "alice@example.com"
        assert user.username == "alice"
        assert user.role == UserRole.ADMIN
        assert user.status == UserStatus.INACTIVE

    def test_applies_default_role_when_not_provided(self):
        create_user_dto = CreateUserDTO(email="bob@example.com", username="bob")

        user = UserEntityConverter.to_entity(create_user_dto)

        assert user.role == UserRole.USER

    def test_applies_default_status_when_not_provided(self):
        create_user_dto = CreateUserDTO(email="bob@example.com", username="bob")

        user = UserEntityConverter.to_entity(create_user_dto)

        assert user.status == UserStatus.ACTIVE
