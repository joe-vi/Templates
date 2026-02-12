# Agent Instructions for FastAPI Clean Architecture Template

This document provides guidance for AI agents (like Claude Code) working with this FastAPI Clean Architecture codebase.

## Architecture Overview

This project follows Clean Architecture principles with four distinct layers:

### Layer Dependencies (Inside → Outside)
```
Domain (Core) → Application → Infrastructure → API
```

**Critical Rule**: Inner layers NEVER depend on outer layers. Dependencies point inward.

## Key Architectural Patterns

### 1. Repository Pattern with ABC Base Classes

All abstract base classes (interfaces) MUST end with `Base`:

```python
# Domain Layer - Interface
class GreetingRepositoryBase(ABC):
    @abstractmethod
    async def create(self, greeting: Greeting) -> Greeting:
        pass

# Infrastructure Layer - Implementation
class GreetingRepository(GreetingRepositoryBase):
    async def create(self, greeting: Greeting) -> Greeting:
        # Implementation here
        pass
```

### 2. ConnectionFactory Pattern with Dependency Injection

The `ConnectionFactory` is injected into repositories to manage database sessions. It provides:
- Async context manager for session lifecycle
- Automatic commit/rollback
- Connection pooling

**Key Principle**: Repositories manage their own sessions using the injected `connection_factory`.

**ConnectionFactoryBase** ([connection_factory_base.py](src/infrastructure/database/connection_factory_base.py)):
```python
class ConnectionFactoryBase(ABC):
    @classmethod
    @abstractmethod
    async def get_session(cls) -> AsyncGenerator[AsyncSession, None]:
        pass
```

**Repository Usage Example**:
```python
class GreetingRepository(GreetingRepositoryBase):
    def __init__(self, connection_factory: ConnectionFactoryBase):
        self._connection_factory = connection_factory

    async def create(self, greeting: Greeting) -> Greeting:
        async with self._connection_factory.get_session() as session:
            # Use session for DB operations
            # Session automatically commits and closes
            pass
```

**Critical Rules**:
- Repositories receive `ConnectionFactoryBase` via dependency injection
- Each repository method creates its own session using `async with self._connection_factory.get_session()`
- Never manually create sessions or pass sessions to repository constructors

### 3. Dependency Injection with fastapi-injector

This application uses `fastapi-injector` which integrates the `injector` library with FastAPI middleware for automatic dependency injection.

**AppModule Setup** ([container.py](src/container.py)):
```python
from injector import Module, Binder, Injector, singleton

class AppModule(Module):
    """Dependency Injection Module using injector.Module."""

    def configure(self, binder: Binder) -> None:
        # Bind ConnectionFactory as singleton (shared across app)
        binder.bind(
            ConnectionFactoryBase,   # Interface (ABC)
            to=ConnectionFactory,    # Implementation
            scope=singleton,         # Singleton scope
        )

        # Bind Repository interfaces to implementations (request scope)
        binder.bind(
            GreetingRepositoryBase,  # Interface (ABC)
            to=GreetingRepository,   # Implementation
        )

        # Bind Use Case interfaces to implementations (request scope)
        binder.bind(
            GreetingUseCaseBase,     # Interface (ABC)
            to=GreetingUseCase,      # Implementation
        )

# Global injector instance
injector = Injector([AppModule()])
```

**Attach Injector Middleware** ([main.py](src/main.py)):
```python
from fastapi_injector import attach_injector
from src.container import injector

app = FastAPI(...)

# Attach injector as middleware
attach_injector(app, injector)
```

**Routes use Injected[Type]** ([greeting_routes.py](src/api/routes/greeting_routes.py)):
```python
from fastapi_injector import Injected

@router.post("/greetings")
async def create_greeting(
    greeting_data: GreetingCreateRequest,
    use_case: GreetingUseCaseBase = Injected(GreetingUseCaseBase),
) -> GreetingResponse:
    create_greeting_dto = GreetingConverter.to_create_dto(greeting_data)
    created_greeting_dto = await use_case.create_greeting(create_greeting_dto)
    return GreetingConverter.to_response(created_greeting_dto)
```

**Critical Rules**:
- Routes MUST use `Injected[BaseClass]` for dependency injection (not `Depends(...)`)
- Routes MUST depend on Base classes (abstractions), never concrete implementations
- Use `Binder.bind(Interface, to=Implementation)` in AppModule.configure()
- Use `singleton` scope for shared resources (e.g., ConnectionFactory)
- The injector automatically resolves the entire dependency chain via constructor injection
- No manual dependency functions needed - fastapi-injector handles everything automatically

## Adding New Features

### Step-by-Step Guide

When adding a new feature (e.g., "User Management"), follow this order:

#### 1. Domain Layer (`src/domain/`)
Create the entity and repository interface:

```python
# src/domain/entities/user.py
@dataclass
class User:
    id: Optional[int]
    name: str
    email: str

# src/domain/repositories/user_repository_base.py
class UserRepositoryBase(ABC):  # Must end with Base
    @abstractmethod
    async def create(self, user: User) -> User:
        pass
```

#### 2. Infrastructure Layer (`src/infrastructure/`)
Create database model and repository implementation:

```python
# src/infrastructure/database/models.py
class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

# src/infrastructure/repositories/user_repository.py
class UserRepository(UserRepositoryBase):
    def __init__(self, connection_factory: ConnectionFactoryBase):
        self._connection_factory = connection_factory

    async def create(self, user: User) -> User:
        async with self._connection_factory.get_session() as session:
            # Implementation using session
            # Session automatically commits and closes
            pass
```

#### 3. Application Layer (`src/application/`)
Create DTOs, converters, use case base class, and use case implementation:

```python
# src/application/dtos/user_dto.py
@dataclass(frozen=True)
class CreateUserDTO:
    name: str
    email: str

@dataclass(frozen=True)
class UserDTO:
    id: int
    name: str
    email: str

# src/application/converters/user_converter.py
class UserEntityConverter:
    @staticmethod
    def to_dto(user: User) -> UserDTO:
        return UserDTO(id=user.id, name=user.name, email=user.email)

    @staticmethod
    def to_entity(create_user_dto: CreateUserDTO) -> User:
        return User(id=None, name=create_user_dto.name, email=create_user_dto.email)

# src/application/use_cases/user_use_case_base.py
class UserUseCaseBase(ABC):  # Must end with Base
    @abstractmethod
    async def create_user(self, create_user_dto: CreateUserDTO) -> UserDTO:
        pass

# src/application/use_cases/user_use_case.py
class UserUseCase(UserUseCaseBase):  # Extends base class
    def __init__(self, repository: UserRepositoryBase):
        self._repository = repository

    async def create_user(self, create_user_dto: CreateUserDTO) -> UserDTO:
        user = UserEntityConverter.to_entity(create_user_dto)
        created_user = await self._repository.create(user)
        return UserEntityConverter.to_dto(created_user)
```

#### 4. Module Bindings (`src/container.py`)
Add bindings to the AppModule using Binder.bind():

```python
# src/container.py
class AppModule(Module):
    def configure(self, binder: Binder) -> None:
        # ConnectionFactory binding (already exists)
        binder.bind(
            ConnectionFactoryBase,  # Interface (ABC)
            to=ConnectionFactory,   # Implementation
        )

        # ... existing repository and use case bindings ...

        # Add new repository binding
        binder.bind(
            UserRepositoryBase,  # Interface (ABC)
            to=UserRepository,   # Implementation
        )

        # Add new use case binding
        binder.bind(
            UserUseCaseBase,     # Interface (ABC)
            to=UserUseCase,      # Implementation
        )
```

#### 5. API Layer (`src/api/`)
Create API schemas, converters, and routes:

```python
# src/api/schemas/user_schema.py
class UserCreateRequest(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

# src/api/converters/user_converter.py
class UserConverter:
    @staticmethod
    def to_create_dto(request: UserCreateRequest) -> CreateUserDTO:
        return CreateUserDTO(name=request.name, email=request.email)

    @staticmethod
    def to_response(user_dto: UserDTO) -> UserResponse:
        return UserResponse(id=user_dto.id, name=user_dto.name, email=user_dto.email)

# src/api/routes/user_routes.py
from fastapi import APIRouter, HTTPException, status
from fastapi_injector import Injected
from src.application.use_cases.user_use_case_base import UserUseCaseBase
from src.api.schemas.user_schema import UserCreateRequest, UserResponse
from src.api.converters.user_converter import UserConverter

router = APIRouter(prefix="/api/v1", tags=["users"])

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    use_case: UserUseCaseBase = Injected(UserUseCaseBase),
) -> UserResponse:
    create_user_dto = UserConverter.to_create_dto(user_data)
    created_user_dto = await use_case.create_user(create_user_dto)
    return UserConverter.to_response(created_user_dto)
```

**Note**: No dependency functions needed! The injector automatically:
1. Resolves `UserUseCaseBase` to `UserUseCase`
2. Injects `UserRepositoryBase` (resolved to `UserRepository`) via constructor
3. Injects `ConnectionFactoryBase` (resolved to `ConnectionFactory` singleton) into repository via constructor

#### 6. Register Routes
Add to [main.py](src/main.py):

```python
from src.api.routes.user_routes import router as user_router

app.include_router(user_router)
```

## Important Conventions

### Class Naming Conventions
- **ABC Classes**: Must end with `Base` (e.g., `RepositoryBase`, `UseCaseBase`)
- **Entities**: Singular nouns (e.g., `User`, `Greeting`, `Product`)
- **API Schemas**: Purpose suffix - `Request` for inputs, `Response` for outputs (e.g., `UserCreateRequest`, `UserResponse`)
- **DTOs**: Frozen dataclasses with `DTO` suffix (e.g., `CreateUserDTO`, `UserDTO`, `UserListDTO`)
- **Use Cases**: Feature + `UseCase` for implementations, Feature + `UseCaseBase` for interfaces
  - Interface: `UserUseCaseBase` (ABC)
  - Implementation: `UserUseCase` (extends UserUseCaseBase)

### Variable and Property Naming Conventions

**Critical Rules** - These MUST be followed for all variables and properties:

1. **Collections use plural names**:
   - `List[Greeting]` → `greetings`
   - `List[GreetingModel]` → `greeting_models`
   - Single object → singular: `Greeting` → `greeting`

2. **Sets use `_set` suffix**:
   - `Set[int]` → `greeting_id_set`

3. **Dictionaries use `_map` suffix**:
   - `Dict[int, Greeting]` → `greeting_map`

4. **Internal properties/variables prefixed with `_`**:
   - Properties that should never be accessed from outside the class MUST be prefixed with `_`
   - `self._repository`, `self._connection_factory`, `self._engine`, `self._session_factory`

5. **Meaningful and complete variable names**:
   - Never use shortforms or abbreviations unless the name would be very long
   - `dto` alone is too vague → use `create_greeting_dto`, `greeting_dto`, `greeting_list_dto`
   - `entity` alone is too vague → use `greeting`, `user`, `order` (the actual domain concept)
   - `result` alone is too vague → use `query_result`, `delete_result`, `greeting_dto`

6. **Boolean variables/properties MUST read like questions**:
   - `is_active`, `is_deleted`, `is_successful`, `is_sql_echo_enabled`
   - `can_update`, `can_delete`
   - `has_items`, `has_permission`
   - Never use bare nouns for booleans: `success` → `is_successful`, `active` → `is_active`

### Async/Await
- ALL database operations are async
- Use `async def` and `await` for DB operations
- AsyncSession from ConnectionFactory
- AsyncGenerator for dependencies

### Error Handling
```python
# In routes
if result is None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resource not found"
    )
```

## Database Migrations

While this template uses `create_all()` for simplicity, in production:

1. Use Alembic for migrations
2. Never use `create_all()` in production
3. Version control all schema changes

## Testing Strategy

When writing tests:

```python
# Mock the repository, not the database
@pytest.mark.asyncio
async def test_create_user():
    mock_repo = Mock(spec=UserRepositoryBase)
    use_case = UserUseCase(repository=mock_repo)

    result = await use_case.create_user("John", "john@example.com")
    mock_repo.create.assert_called_once()
```

## Common Patterns

### Handling Transactions
```python
# Repositories manage their own sessions
# Transactions are automatic within each repository method
class SomeRepository(SomeRepositoryBase):
    def __init__(self, connection_factory: ConnectionFactoryBase):
        self._connection_factory = connection_factory

    async def operation_1(self) -> None:
        async with self._connection_factory.get_session() as session:
            # DB operations here
            # Auto-commit on success, rollback on exception
            pass

    async def operation_2(self) -> None:
        async with self._connection_factory.get_session() as session:
            # DB operations here
            pass
```

### Multiple Repository Operations

With fastapi-injector, use cases with multiple repository dependencies are automatically resolved via constructor injection:

```python
# Use case with multiple repositories
class MultiUseCase(MultiUseCaseBase):
    def __init__(
        self,
        user_repository: UserRepositoryBase,
        order_repository: OrderRepositoryBase,
    ):
        self._user_repository = user_repository
        self._order_repository = order_repository

    async def process_order(self, user_id: int, order_data: dict) -> Order:
        # Both repositories have ConnectionFactory injected automatically
        user = await self._user_repository.get_by_id(user_id)
        order = await self._order_repository.create(order_data)
        return order

# In routes - automatic injection of use case with all dependencies
@router.post("/orders")
async def create_order(
    order_data: OrderCreateRequest,
    use_case: MultiUseCaseBase = Injected(MultiUseCaseBase),
) -> OrderResponse:
    order = await use_case.process_order(order_data.user_id, order_data)
    return OrderResponse(**order.__dict__)
```

### Adding New Bindings to AppModule
```python
# In src/container.py
from injector import Module, Binder, singleton

class AppModule(Module):
    def configure(self, binder: Binder) -> None:
        # Bind ConnectionFactory as singleton (required for all repositories)
        binder.bind(
            ConnectionFactoryBase,  # Interface (ABC)
            to=ConnectionFactory,   # Implementation class
            scope=singleton,        # Singleton scope
        )

        # ... existing repository and use case bindings ...

        # Bind new repository using Binder.bind() (request scope by default)
        binder.bind(
            NewRepositoryBase,  # Interface (ABC)
            to=NewRepository,   # Implementation class
        )

        # Bind new use case using Binder.bind() (request scope by default)
        binder.bind(
            NewUseCaseBase,     # Interface (ABC)
            to=NewUseCase,      # Implementation class
        )
```

## Configuration

Environment variables are managed in:
- [config.py](src/infrastructure/database/config.py) - Database settings
- [.env](.env.example) - Environment file (copy from .env.example)

Never hardcode configuration values.

## Debugging Tips

1. **Enable SQL Logging**: Set `IS_SQL_ECHO_ENABLED=true` in .env
2. **Check Sessions**: Ensure `async with self._connection_factory.get_session()` is used in repositories
3. **Verify DI**: Ensure `attach_injector(app, injector)` is called in main.py before adding routes
4. **Check Bindings**: Verify all base classes are bound in AppModule.configure()
5. **Injection Errors**: If `Injected[Type]` doesn't work, ensure:
   - fastapi-injector middleware is attached
   - Type is bound in AppModule
   - Using base class, not concrete implementation
6. **Layer Violations**: Ensure no circular imports (Domain should never import from Infrastructure)

## Anti-Patterns to Avoid

❌ **Don't pass sessions to repository constructors**:
```python
# Wrong - repositories should not receive sessions
class UserRepository(UserRepositoryBase):
    def __init__(self, session: AsyncSession):
        self.session = session

# Correct - repositories receive ConnectionFactoryBase
class UserRepository(UserRepositoryBase):
    def __init__(self, connection_factory: ConnectionFactoryBase):
        self._connection_factory = connection_factory
```

❌ **Don't use Depends() with manual dependency functions**:
```python
# Wrong - using old FastAPI Depends pattern
from fastapi import Depends

@router.post("/users")
async def create_user(
    use_case: UserUseCaseBase = Depends(get_user_use_case),  # Wrong!
):
    pass

# Correct - use Injected[Type] with fastapi-injector
from fastapi_injector import Injected

@router.post("/users")
async def create_user(
    use_case: Injected[UserUseCaseBase],  # Correct!
) -> UserResponseSchema:
    pass
```

❌ **Don't bypass use cases in routes**:
```python
# Wrong
@router.post("/users")
async def create_user(repo: UserRepository = Depends(get_repo)):
    return await repo.create(...)  # Skip use case
```

❌ **Don't let Domain depend on Infrastructure**:
```python
# Wrong - in domain layer
from src.infrastructure.database.models import UserModel  # ❌
```

❌ **Don't forget Base suffix on ABC classes**:
```python
# Wrong
class UserRepository(ABC):  # Should be UserRepositoryBase
class UserUseCase(ABC):  # Should be UserUseCaseBase
```

❌ **Don't use concrete types in route signatures**:
```python
# Wrong - using concrete implementation
@router.post("/users")
async def create_user(use_case: Injected[UserUseCase]):  # Concrete type!
    pass

# Correct - using base class
@router.post("/users")
async def create_user(use_case: Injected[UserUseCaseBase]):  # Base class!
    pass
```

❌ **Don't create instances manually**:
```python
# Wrong - manual instantiation
async def get_user_use_case():
    connection_factory = ConnectionFactory()
    repo = UserRepository(connection_factory)  # Direct instantiation
    yield UserUseCase(repo)

# Correct - use Injected[Type] with fastapi-injector
# No dependency function needed!
@router.post("/users")
async def create_user(
    use_case: Injected[UserUseCaseBase],  # Automatic injection!
) -> UserResponseSchema:
    pass
```

❌ **Don't forget to add bindings to AppModule**:
```python
# Wrong - forgetting to add to AppModule
# You create UserUseCase but don't bind it

# Correct - always add bindings with Binder.bind()
class AppModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(UserRepositoryBase, to=UserRepository)
        binder.bind(UserUseCaseBase, to=UserUseCase)
```

❌ **Don't forget to attach injector middleware**:
```python
# Wrong - creating app without attaching injector
app = FastAPI()
app.include_router(user_router)  # Injected[Type] won't work!

# Correct - attach injector middleware
from fastapi_injector import attach_injector
from src.container import injector

app = FastAPI()
attach_injector(app, injector)  # Enable automatic injection
app.include_router(user_router)
```

❌ **Don't use singleton scope for request-scoped dependencies**:
```python
# Wrong - repositories/use cases shouldn't be singletons
binder.bind(UserRepositoryBase, to=UserRepository, scope=singleton)

# Correct - only ConnectionFactory should be singleton
binder.bind(ConnectionFactoryBase, to=ConnectionFactory, scope=singleton)  # ✓
binder.bind(UserRepositoryBase, to=UserRepository)  # Request scope (default) ✓
```

✅ **Correct patterns are shown in the examples above**.

## Quick Reference

| Layer | Location | Contains | Depends On |
|-------|----------|----------|------------|
| Domain | `src/domain/` | Entities, Repository ABC (ending with Base) | Nothing |
| Application | `src/application/` | Use case ABC/implementations, DTOs, Entity converters | Domain only |
| Infrastructure | `src/infrastructure/` | DB models, Repository implementations | Domain, Application |
| API | `src/api/` | Routes, Request/Response schemas, API converters | Application (Base classes) |
| AppModule | `src/container.py` | DI module with injector.Module and Binder.bind() | All layers |

## Questions?

Refer to existing code in the template:
- [Greeting entity](src/domain/entities/greeting.py)
- [Repository Base](src/domain/repositories/greeting_repository_base.py)
- [Repository implementation](src/infrastructure/repositories/greeting_repository.py)
- [DTOs](src/application/dtos/greeting_dto.py)
- [Entity converter](src/application/converters/greeting_converter.py)
- [Use case Base](src/application/use_cases/greeting_use_case_base.py)
- [Use case implementation](src/application/use_cases/greeting_use_case.py)
- [API schemas](src/api/schemas/greeting_schema.py)
- [API converter](src/api/converters/greeting_converter.py)
- [Routes](src/api/routes/greeting_routes.py)
- [DI Container](src/container.py)
- [Main app](src/main.py)
