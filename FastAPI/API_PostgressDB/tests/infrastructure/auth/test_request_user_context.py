import pytest
from injector import Binder, Injector, Module

from src.domain.enums import user_enum
from src.infrastructure.auth.request_user_context import RequestUserContext
from src.infrastructure.di.request_scope import request, request_scope
from src.infrastructure.di.typed_binder import TypedBinder
from src.ports.user_context import UserContext


class TestPopulate:
    def test_reads_back_identity_after_populate(self):
        user_context = RequestUserContext()

        user_context.populate(42, user_enum.UserRole.ADMIN)

        assert user_context.user_id == 42
        assert user_context.role == user_enum.UserRole.ADMIN

    def test_second_populate_raises(self):
        user_context = RequestUserContext()
        user_context.populate(1, user_enum.UserRole.USER)

        with pytest.raises(RuntimeError, match="more than once"):
            user_context.populate(2, user_enum.UserRole.ADMIN)

    def test_failed_second_populate_keeps_original_identity(self):
        user_context = RequestUserContext()
        user_context.populate(1, user_enum.UserRole.USER)

        with pytest.raises(RuntimeError):
            user_context.populate(2, user_enum.UserRole.ADMIN)

        assert user_context.user_id == 1
        assert user_context.role == user_enum.UserRole.USER


class TestUnpopulatedAccess:
    def test_user_id_is_none_before_populate(self):
        assert RequestUserContext().user_id is None

    def test_role_is_none_before_populate(self):
        assert RequestUserContext().role is None


class _WiringModule(Module):
    def configure(self, binder: Binder) -> None:
        TypedBinder(binder).bind_typed(UserContext).to(RequestUserContext, scope=request)


class TestRequestScopeBinding:
    def test_same_instance_within_one_request(self):
        injector = Injector([_WiringModule()])

        with request_scope():
            first = injector.get(UserContext)
            first.populate(7, user_enum.UserRole.USER)
            second = injector.get(UserContext)

            assert second is first
            assert second.user_id == 7

    def test_fresh_empty_instance_per_request(self):
        """Identity can never leak from one request into the next."""
        injector = Injector([_WiringModule()])

        with request_scope():
            injector.get(UserContext).populate(7, user_enum.UserRole.ADMIN)

        with request_scope():
            next_request_context = injector.get(UserContext)
            assert next_request_context.user_id is None
            assert next_request_context.role is None
