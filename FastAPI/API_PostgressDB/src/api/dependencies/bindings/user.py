from src.application.use_cases.user.create_user_use_case import CreateUserUseCase
from src.application.use_cases.user.delete_user_use_case import DeleteUserUseCase
from src.application.use_cases.user.get_all_users_use_case import GetAllUsersUseCase
from src.application.use_cases.user.get_user_use_case import GetUserUseCase
from src.application.use_cases.user.update_user_role_use_case import UpdateUserRoleUseCase
from src.domain.repositories.user.user_repository import UserRepository
from src.infrastructure.di.typed_binder import TypedBinder
from src.infrastructure.repositories.user.sqlalchemy_user_repository import SqlAlchemyUserRepository


def register(typed_binder: TypedBinder) -> None:
    """Bind the user domain's repository and use cases (all transient)."""
    typed_binder.bind_typed(UserRepository).to(SqlAlchemyUserRepository)
    typed_binder.bind_self_typed(CreateUserUseCase)
    typed_binder.bind_self_typed(GetUserUseCase)
    typed_binder.bind_self_typed(GetAllUsersUseCase)
    typed_binder.bind_self_typed(UpdateUserRoleUseCase)
    typed_binder.bind_self_typed(DeleteUserUseCase)
