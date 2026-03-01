"""Unit tests for UserConverter (API layer)."""

from datetime import datetime

from src.api.routers.user import user_converter, user_schema
from src.application.use_cases.user import user_dto as user_dto_module
from src.domain.enums import user_enum


def _make_user_dto(user_id: int = 1) -> user_dto_module.UserDTO:
    return user_dto_module.UserDTO(
        id=user_id,
        email="alice@example.com",
        username="alice",
        role=user_enum.UserRole.USER,
        status=user_enum.UserStatus.ACTIVE,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


class TestToCreateDto:
    def test_maps_all_fields_from_request(self):
        request = user_schema.UserCreateRequest(
            email="alice@example.com",
            username="alice",
            password="TestPass123",
            role=user_enum.UserRole.ADMIN,
            status=user_enum.UserStatus.INACTIVE,
        )

        create_dto = user_converter.UserConverter.to_create_dto(request)

        assert isinstance(create_dto, user_dto_module.CreateUserDTO)
        assert create_dto.email == "alice@example.com"
        assert create_dto.username == "alice"
        assert create_dto.password == "TestPass123"
        assert create_dto.role == user_enum.UserRole.ADMIN
        assert create_dto.status == user_enum.UserStatus.INACTIVE

    def test_applies_default_role_from_request_schema(self):
        request = user_schema.UserCreateRequest(
            email="bob@example.com", username="bob", password="TestPass123"
        )

        create_dto = user_converter.UserConverter.to_create_dto(request)

        assert create_dto.role == user_enum.UserRole.USER

    def test_applies_default_status_from_request_schema(self):
        request = user_schema.UserCreateRequest(
            email="bob@example.com", username="bob", password="TestPass123"
        )

        create_dto = user_converter.UserConverter.to_create_dto(request)

        assert create_dto.status == user_enum.UserStatus.ACTIVE


class TestToUpdateRoleDto:
    def test_maps_user_id_and_role_from_request(self):
        request = user_schema.UserUpdateRoleRequest(
            role=user_enum.UserRole.ADMIN
        )

        update_dto = user_converter.UserConverter.to_update_role_dto(
            user_id=5, request=request
        )

        assert isinstance(update_dto, user_dto_module.UpdateUserRoleDTO)
        assert update_dto.user_id == 5
        assert update_dto.role == user_enum.UserRole.ADMIN

    def test_preserves_role_enum_value(self):
        request = user_schema.UserUpdateRoleRequest(
            role=user_enum.UserRole.USER
        )

        update_dto = user_converter.UserConverter.to_update_role_dto(
            user_id=1, request=request
        )

        assert update_dto.role == user_enum.UserRole.USER


class TestToResponse:
    def test_maps_all_fields_from_dto(self):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        user_dto = user_dto_module.UserDTO(
            id=1,
            email="alice@example.com",
            username="alice",
            role=user_enum.UserRole.ADMIN,
            status=user_enum.UserStatus.INACTIVE,
            created_at=created_at,
        )

        response = user_converter.UserConverter.to_response(user_dto)

        assert isinstance(response, user_schema.UserResponse)
        assert response.id == 1
        assert response.email == "alice@example.com"
        assert response.username == "alice"
        assert response.role == user_enum.UserRole.ADMIN
        assert response.status == user_enum.UserStatus.INACTIVE
        assert response.created_at == created_at

    def test_preserves_enum_values(self):
        user_dto = _make_user_dto()

        response = user_converter.UserConverter.to_response(user_dto)

        assert response.role == user_enum.UserRole.USER
        assert response.status == user_enum.UserStatus.ACTIVE


class TestToResponseList:
    def test_maps_each_dto_to_response(self):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        user_dtos = [
            user_dto_module.UserDTO(
                id=1,
                email="alice@example.com",
                username="alice",
                role=user_enum.UserRole.USER,
                status=user_enum.UserStatus.ACTIVE,
                created_at=created_at,
            ),
            user_dto_module.UserDTO(
                id=2,
                email="bob@example.com",
                username="bob",
                role=user_enum.UserRole.ADMIN,
                status=user_enum.UserStatus.INACTIVE,
                created_at=created_at,
            ),
        ]

        responses = user_converter.UserConverter.to_response_list(user_dtos)

        assert len(responses) == 2
        assert responses[0].id == 1
        assert responses[0].email == "alice@example.com"
        assert responses[1].id == 2
        assert responses[1].email == "bob@example.com"

    def test_returns_empty_list_when_given_no_dtos(self):
        responses = user_converter.UserConverter.to_response_list([])

        assert responses == []

    def test_preserves_order_of_dtos(self):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        user_dtos = [
            user_dto_module.UserDTO(
                id=id,
                email=f"user{id}@example.com",
                username=f"user{id}",
                role=user_enum.UserRole.USER,
                status=user_enum.UserStatus.ACTIVE,
                created_at=created_at,
            )
            for id in [3, 1, 2]
        ]

        responses = user_converter.UserConverter.to_response_list(user_dtos)

        assert [r.id for r in responses] == [3, 1, 2]
