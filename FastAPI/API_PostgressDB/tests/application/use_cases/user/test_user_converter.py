"""Unit tests for UserEntityConverter."""

from datetime import datetime

from src.application.use_cases.user import user_converter
from src.application.use_cases.user import user_dto as user_dto_module
from src.domain.entities.user import user as user_module
from src.domain.enums import user_enum


def _make_user(user_id: int = 1) -> user_module.User:
    return user_module.User(
        id=user_id,
        email="alice@example.com",
        username="alice",
        role=user_enum.UserRole.ADMIN,
        status=user_enum.UserStatus.ACTIVE,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


class TestToDto:
    def test_maps_all_fields_from_entity(self):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        user = user_module.User(
            id=1,
            email="alice@example.com",
            username="alice",
            role=user_enum.UserRole.ADMIN,
            status=user_enum.UserStatus.INACTIVE,
            created_at=created_at,
        )

        result_dto = user_converter.UserEntityConverter.to_dto(user)

        assert isinstance(result_dto, user_dto_module.UserDTO)
        assert result_dto.id == 1
        assert result_dto.email == "alice@example.com"
        assert result_dto.username == "alice"
        assert result_dto.role == user_enum.UserRole.ADMIN
        assert result_dto.status == user_enum.UserStatus.INACTIVE
        assert result_dto.created_at == created_at

    def test_preserves_user_role_enum(self):
        user = _make_user()
        result_dto = user_converter.UserEntityConverter.to_dto(user)
        assert result_dto.role == user_enum.UserRole.ADMIN

    def test_preserves_user_status_enum(self):
        user = user_module.User(
            id=1,
            email="bob@example.com",
            username="bob",
            role=user_enum.UserRole.USER,
            status=user_enum.UserStatus.INACTIVE,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )
        result_dto = user_converter.UserEntityConverter.to_dto(user)
        assert result_dto.status == user_enum.UserStatus.INACTIVE


class TestToDtoList:
    def test_maps_each_user_to_dto(self):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        users = [
            user_module.User(
                id=1,
                email="alice@example.com",
                username="alice",
                role=user_enum.UserRole.ADMIN,
                status=user_enum.UserStatus.ACTIVE,
                created_at=created_at,
            ),
            user_module.User(
                id=2,
                email="bob@example.com",
                username="bob",
                role=user_enum.UserRole.USER,
                status=user_enum.UserStatus.INACTIVE,
                created_at=created_at,
            ),
        ]

        user_dtos = user_converter.UserEntityConverter.to_dto_list(users)

        assert len(user_dtos) == 2
        assert user_dtos[0].id == 1
        assert user_dtos[0].email == "alice@example.com"
        assert user_dtos[1].id == 2
        assert user_dtos[1].email == "bob@example.com"

    def test_returns_empty_list_when_given_no_users(self):
        user_dtos = user_converter.UserEntityConverter.to_dto_list([])
        assert user_dtos == []

    def test_preserves_order_of_users(self):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        users = [
            user_module.User(
                id=id,
                email=f"user{id}@example.com",
                username=f"user{id}",
                role=user_enum.UserRole.USER,
                status=user_enum.UserStatus.ACTIVE,
                created_at=created_at,
            )
            for id in [3, 1, 2]
        ]

        user_dtos = user_converter.UserEntityConverter.to_dto_list(users)

        assert [dto.id for dto in user_dtos] == [3, 1, 2]


class TestToEntity:
    def test_sets_id_to_none(self):
        create_user_dto = user_dto_module.CreateUserDTO(
            email="alice@example.com", username="alice", password="TestPass123"
        )

        user = user_converter.UserEntityConverter.to_entity(
            create_user_dto, "hashed_password"
        )

        assert user.id is None

    def test_maps_all_fields_from_dto(self):
        create_user_dto = user_dto_module.CreateUserDTO(
            email="alice@example.com",
            username="alice",
            password="TestPass123",
            role=user_enum.UserRole.ADMIN,
            status=user_enum.UserStatus.INACTIVE,
        )

        user = user_converter.UserEntityConverter.to_entity(
            create_user_dto, "hashed_password"
        )

        assert isinstance(user, user_module.User)
        assert user.email == "alice@example.com"
        assert user.username == "alice"
        assert user.role == user_enum.UserRole.ADMIN
        assert user.status == user_enum.UserStatus.INACTIVE

    def test_applies_default_role_when_not_provided(self):
        create_user_dto = user_dto_module.CreateUserDTO(
            email="bob@example.com", username="bob", password="TestPass123"
        )

        user = user_converter.UserEntityConverter.to_entity(
            create_user_dto, "hashed_password"
        )

        assert user.role == user_enum.UserRole.USER

    def test_applies_default_status_when_not_provided(self):
        create_user_dto = user_dto_module.CreateUserDTO(
            email="bob@example.com", username="bob", password="TestPass123"
        )

        user = user_converter.UserEntityConverter.to_entity(
            create_user_dto, "hashed_password"
        )

        assert user.status == user_enum.UserStatus.ACTIVE
