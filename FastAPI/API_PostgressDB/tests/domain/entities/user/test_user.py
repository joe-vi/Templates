import pytest

from src.domain.entities.user.user import User
from src.domain.enums import user_enum


def _make_user(**overrides: object) -> User:
    values: dict = {"id": 1, "email": "alice@example.com", "username": "alice"}
    values.update(overrides)
    return User(**values)


class TestInvariants:
    def test_valid_user_is_constructed(self):
        user = _make_user()

        assert user.email == "alice@example.com"
        assert user.username == "alice"

    def test_blank_username_is_rejected(self):
        with pytest.raises(ValueError, match="username"):
            _make_user(username="   ")

    def test_blank_email_is_rejected(self):
        with pytest.raises(ValueError, match="email"):
            _make_user(email="")

    @pytest.mark.parametrize("bad_email", ["not-an-email", "@example.com", "alice@", "alice"])
    def test_malformed_email_is_rejected(self, bad_email: str):
        with pytest.raises(ValueError, match="not a valid email"):
            _make_user(email=bad_email)

    def test_defaults_are_user_role_and_active_status(self):
        user = _make_user()

        assert user.role is user_enum.UserRole.USER
        assert user.status is user_enum.UserStatus.ACTIVE


class TestPersistenceState:
    def test_unpersisted_user_has_no_id(self):
        user = _make_user(id=None)

        assert user.is_persisted is False

    def test_persisted_user_has_id(self):
        user = _make_user(id=7)

        assert user.is_persisted is True


class TestLifecycle:
    def test_active_user_is_active(self):
        user = _make_user(status=user_enum.UserStatus.ACTIVE)

        assert user.is_active is True

    def test_inactive_user_is_not_active(self):
        user = _make_user(status=user_enum.UserStatus.INACTIVE)

        assert user.is_active is False

    def test_deactivate_blocks_the_user(self):
        user = _make_user()

        user.deactivate()

        assert user.is_active is False
        assert user.status is user_enum.UserStatus.INACTIVE

    def test_activate_restores_the_user(self):
        user = _make_user(status=user_enum.UserStatus.INACTIVE)

        user.activate()

        assert user.is_active is True
        assert user.status is user_enum.UserStatus.ACTIVE
