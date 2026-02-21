from datetime import datetime

from src.api.routers.user.user_converter import UserConverter
from src.api.routers.user.user_schema import UserCreateRequest, UserResponse, UserUpdateRoleRequest
from src.application.use_cases.user.user_dto import CreateUserDTO, UpdateUserRoleDTO, UserDTO
from src.domain.enums.user_enum import UserRole, UserStatus


def _make_user_dto(user_id: int = 1) -> UserDTO:
    return UserDTO(
        id=user_id,
        email="alice@example.com",
        username="alice",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


class TestToCreateDto:
    def test_maps_all_fields_from_request(self):
        request = UserCreateRequest(
            email="alice@example.com",
            username="alice",
            password="TestPass123",
            role=UserRole.ADMIN,
            status=UserStatus.INACTIVE,
        )

        create_dto = UserConverter.to_create_dto(request)

        assert isinstance(create_dto, CreateUserDTO)
        assert create_dto.email == "alice@example.com"
        assert create_dto.username == "alice"
        assert create_dto.password == "TestPass123"
        assert create_dto.role == UserRole.ADMIN
        assert create_dto.status == UserStatus.INACTIVE

    def test_applies_default_role_from_request_schema(self):
        request = UserCreateRequest(email="bob@example.com", username="bob", password="TestPass123")

        create_dto = UserConverter.to_create_dto(request)

        assert create_dto.role == UserRole.USER

    def test_applies_default_status_from_request_schema(self):
        request = UserCreateRequest(email="bob@example.com", username="bob", password="TestPass123")

        create_dto = UserConverter.to_create_dto(request)

        assert create_dto.status == UserStatus.ACTIVE


class TestToUpdateRoleDto:
    def test_maps_user_id_and_role_from_request(self):
        request = UserUpdateRoleRequest(role=UserRole.ADMIN)

        update_dto = UserConverter.to_update_role_dto(user_id=5, request=request)

        assert isinstance(update_dto, UpdateUserRoleDTO)
        assert update_dto.user_id == 5
        assert update_dto.role == UserRole.ADMIN

    def test_preserves_role_enum_value(self):
        request = UserUpdateRoleRequest(role=UserRole.USER)

        update_dto = UserConverter.to_update_role_dto(user_id=1, request=request)

        assert update_dto.role == UserRole.USER


class TestToResponse:
    def test_maps_all_fields_from_dto(self):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        user_dto = UserDTO(
            id=1,
            email="alice@example.com",
            username="alice",
            role=UserRole.ADMIN,
            status=UserStatus.INACTIVE,
            created_at=created_at,
        )

        response = UserConverter.to_response(user_dto)

        assert isinstance(response, UserResponse)
        assert response.id == 1
        assert response.email == "alice@example.com"
        assert response.username == "alice"
        assert response.role == UserRole.ADMIN
        assert response.status == UserStatus.INACTIVE
        assert response.created_at == created_at

    def test_preserves_enum_values(self):
        user_dto = _make_user_dto()

        response = UserConverter.to_response(user_dto)

        assert response.role == UserRole.USER
        assert response.status == UserStatus.ACTIVE


class TestToResponseList:
    def test_maps_each_dto_to_response(self):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        user_dtos = [
            UserDTO(id=1, email="alice@example.com", username="alice", role=UserRole.USER, status=UserStatus.ACTIVE, created_at=created_at),
            UserDTO(id=2, email="bob@example.com", username="bob", role=UserRole.ADMIN, status=UserStatus.INACTIVE, created_at=created_at),
        ]

        responses = UserConverter.to_response_list(user_dtos)

        assert len(responses) == 2
        assert responses[0].id == 1
        assert responses[0].email == "alice@example.com"
        assert responses[1].id == 2
        assert responses[1].email == "bob@example.com"

    def test_returns_empty_list_when_given_no_dtos(self):
        responses = UserConverter.to_response_list([])

        assert responses == []

    def test_preserves_order_of_dtos(self):
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        user_dtos = [
            UserDTO(id=id, email=f"user{id}@example.com", username=f"user{id}", role=UserRole.USER, status=UserStatus.ACTIVE, created_at=created_at)
            for id in [3, 1, 2]
        ]

        responses = UserConverter.to_response_list(user_dtos)

        assert [r.id for r in responses] == [3, 1, 2]
