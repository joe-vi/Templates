from datetime import datetime

from src.application.use_cases.user import user_contracts, user_converter
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


class TestToResponse:
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

        result = user_converter.to_response(user)

        assert isinstance(result, user_contracts.UserResponse)
        assert result.id == 1
        assert result.email == "alice@example.com"
        assert result.username == "alice"
        assert result.role == user_enum.UserRole.ADMIN
        assert result.status == user_enum.UserStatus.INACTIVE
        assert result.created_at == created_at

    def test_preserves_user_role_enum(self):
        user = _make_user()
        result = user_converter.to_response(user)
        assert result.role == user_enum.UserRole.ADMIN

    def test_preserves_user_status_enum(self):
        user = user_module.User(
            id=1,
            email="bob@example.com",
            username="bob",
            role=user_enum.UserRole.USER,
            status=user_enum.UserStatus.INACTIVE,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )
        result = user_converter.to_response(user)
        assert result.status == user_enum.UserStatus.INACTIVE


class TestToResponseList:
    def test_maps_each_user_to_response(self):
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

        user_responses = user_converter.to_response_list(users)

        assert len(user_responses) == 2
        assert user_responses[0].id == 1
        assert user_responses[0].email == "alice@example.com"
        assert user_responses[1].id == 2
        assert user_responses[1].email == "bob@example.com"

    def test_returns_empty_list_when_given_no_users(self):
        user_responses = user_converter.to_response_list([])
        assert user_responses == []

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

        user_responses = user_converter.to_response_list(users)

        assert [response.id for response in user_responses] == [3, 1, 2]


class TestToEntity:
    def test_sets_id_to_none(self):
        create_user_request = user_contracts.CreateUserRequest(email="alice@example.com", username="alice", password="TestPass123")

        user = user_converter.to_entity(create_user_request, "hashed_password")

        assert user.id is None

    def test_maps_all_fields_from_request(self):
        create_user_request = user_contracts.CreateUserRequest(
            email="alice@example.com",
            username="alice",
            password="TestPass123",
            role=user_enum.UserRole.ADMIN,
            status=user_enum.UserStatus.INACTIVE,
        )

        user = user_converter.to_entity(create_user_request, "hashed_password")

        assert isinstance(user, user_module.User)
        assert user.email == "alice@example.com"
        assert user.username == "alice"
        assert user.role == user_enum.UserRole.ADMIN
        assert user.status == user_enum.UserStatus.INACTIVE

    def test_applies_default_role_when_not_provided(self):
        create_user_request = user_contracts.CreateUserRequest(email="bob@example.com", username="bob", password="TestPass123")

        user = user_converter.to_entity(create_user_request, "hashed_password")

        assert user.role == user_enum.UserRole.USER

    def test_applies_default_status_when_not_provided(self):
        create_user_request = user_contracts.CreateUserRequest(email="bob@example.com", username="bob", password="TestPass123")

        user = user_converter.to_entity(create_user_request, "hashed_password")

        assert user.status == user_enum.UserStatus.ACTIVE
