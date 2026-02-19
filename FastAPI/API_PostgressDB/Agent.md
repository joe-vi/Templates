# Agent Instructions for FastAPI Clean Architecture Template

This document provides guidance for AI agents working with this FastAPI Clean Architecture codebase.

## Architecture Overview

This project follows Clean Architecture with four distinct layers:

```
Domain (Core) → Application → Infrastructure → API
```

**Critical Rule**: Inner layers NEVER depend on outer layers. Dependencies point inward.

| Layer | Location | Contains | Depends On |
|-------|----------|----------|------------|
| Domain | `src/domain/` | Entities, Repository ABC (ending with `Base`) | Nothing |
| Application | `src/application/` | Use case ABC/implementations, DTOs, Entity converters, External service ABC (ending with `Base`) | Domain only |
| Infrastructure | `src/infrastructure/` | DB models, Repository implementations | Domain, Application |
| API | `src/api/` | Routes, Request/Response schemas, API converters | Application (Base classes) |
| DI Container | `src/container.py` | DI module with `injector.Module` and `Binder.bind()` | All layers |

## Key Architectural Patterns

### 1. Repository Pattern with ABC Base Classes

All abstract base classes (interfaces) MUST end with `Base`:

```python
# Domain Layer - Interface (has docstrings)
class GreetingRepositoryBase(ABC):
    @abstractmethod
    async def create(self, greeting: Greeting) -> Greeting:
        """Persist a new greeting entity.

        Args:
            greeting: The greeting entity to persist.

        Returns:
            The persisted Greeting entity with generated id and timestamps.
        """
        pass

# Infrastructure Layer - Implementation (NO docstrings on overriding methods)
class GreetingRepository(GreetingRepositoryBase):
    def __init__(self, connection_factory: ConnectionFactoryBase):
        self._connection_factory = connection_factory

    async def create(self, greeting: Greeting) -> Greeting:
        async with self._connection_factory.get_session() as session:
            # Implementation here
            pass
```

### 2. ConnectionFactory Pattern

The `ConnectionFactory` is injected into repositories to manage database sessions:
- Async context manager for session lifecycle
- Automatic commit/rollback
- Connection pooling

**Critical Rules**:
- Repositories receive `ConnectionFactoryBase` via constructor injection
- Each repository method creates its own session using `async with self._connection_factory.get_session()`
- Never manually create sessions or pass sessions to repository constructors

### 3. Dependency Injection with fastapi-injector

Uses `fastapi-injector` which integrates the `injector` library with FastAPI middleware.

**AppModule Setup** ([container.py](src/container.py)):
```python
class AppModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(ConnectionFactoryBase, to=ConnectionFactory, scope=singleton)
        binder.bind(GreetingRepositoryBase, to=GreetingRepository)
        binder.bind(GreetingUseCaseBase, to=GreetingUseCase)

injector = Injector([AppModule()])
```

**Attach Middleware** ([main.py](src/main.py)):
```python
attach_injector(app, injector)
```

**Route Injection** ([greeting_routes.py](src/api/routes/greeting_routes.py)):
```python
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
- Routes MUST use `Injected(BaseClass)` for DI (not `Depends(...)`)
- Routes MUST depend on Base classes (abstractions), never concrete implementations
- Use `singleton` scope only for shared resources (e.g., ConnectionFactory)
- The injector automatically resolves the entire dependency chain via constructor injection

## Adding New Features

When adding a new feature (e.g., "User Management"), follow this order:

#### 1. Domain Layer (`src/domain/`)

```python
# src/domain/enums/user_enum.py — define any enums the entity needs
from enum import StrEnum

class UserStatus(StrEnum):
    """Represents the lifecycle status of a user."""
    ACTIVE = "active"
    SUSPENDED = "suspended"

# src/domain/entities/user.py
from dataclasses import field
from src.domain.enums.user_enum import UserStatus

@dataclass
class User:
    id: int | None
    name: str
    email: str
    status: UserStatus = field(default=UserStatus.ACTIVE)

# src/domain/repositories/user_repository_base.py
class UserRepositoryBase(ABC):  # Must end with Base
    @abstractmethod
    async def create(self, user: User) -> User:
        """Persist a new user entity.

        Args:
            user: The user entity to persist.

        Returns:
            The persisted User entity with generated id.
        """
        pass
```

#### 2. Infrastructure Layer (`src/infrastructure/`)

```python
# src/infrastructure/database/models.py (add to existing models.py)
from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.database.db import Base  # Base lives in db.py

class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)

# src/infrastructure/repositories/user_repository.py
class UserRepository(UserRepositoryBase):
    def __init__(self, connection_factory: ConnectionFactoryBase):
        self._connection_factory = connection_factory

    async def create(self, user: User) -> User:
        async with self._connection_factory.get_session() as session:
            # Implementation — no docstring needed (base class has it)
            pass
```

#### 3. Application Layer (`src/application/`)

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
        """Create a new user.

        Args:
            create_user_dto: The DTO containing the user data to create.

        Returns:
            A UserDTO representing the newly created user.
        """
        pass

# src/application/use_cases/user_use_case.py
class UserUseCase(UserUseCaseBase):
    def __init__(self, repository: UserRepositoryBase):
        self._repository = repository

    async def create_user(self, create_user_dto: CreateUserDTO) -> UserDTO:
        user = UserEntityConverter.to_entity(create_user_dto)
        created_user = await self._repository.create(user)
        return UserEntityConverter.to_dto(created_user)
```

#### 4. API Layer (`src/api/`)

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

#### 5. Register Bindings and Routes

```python
# src/container.py — add to AppModule.configure()
binder.bind(UserRepositoryBase, to=UserRepository)
binder.bind(UserUseCaseBase, to=UserUseCase)

# src/main.py — register router
from src.api.routes.user_routes import router as user_router
app.include_router(user_router)
```

**Note**: The injector automatically resolves the full dependency chain — no manual wiring needed.

## Important Conventions

### Class Naming Conventions

- **ABC Classes**: Must end with `Base` (e.g., `RepositoryBase`, `UseCaseBase`)
- **Entities**: Singular nouns (e.g., `User`, `Greeting`)
- **Enums**: Singular noun describing the concept with `StrEnum` (e.g., `GreetingStatus`, `OrderState`)
- **API Schemas**: `Request` for inputs, `Response` for outputs (e.g., `UserCreateRequest`, `UserResponse`)
- **DTOs**: Frozen dataclasses with `DTO` suffix (e.g., `CreateUserDTO`, `UserDTO`, `UserListDTO`)
- **Use Cases**: `UserUseCaseBase` (ABC) → `UserUseCase` (implementation)

### Enum Conventions

**Critical Rules** — MUST be followed for all enums:

1. **Enums belong in the Domain layer** at `src/domain/enums/<feature>_enum.py` — they represent domain concepts and can be imported by any layer
2. **Use `StrEnum`** (Python 3.11+) — values are strings, compatible with Pydantic and SQLAlchemy without extra configuration
3. **Values are lowercase strings** matching what gets stored in the database: `ACTIVE = "active"`
4. **SQLAlchemy models** use `Enum as SQLAlchemyEnum` from `sqlalchemy` with a named type: `Column(SQLAlchemyEnum(GreetingStatus, name="greeting_status"), nullable=False)`
5. **Enums flow through all layers unchanged** — entity → DTO → API schema all use the same enum type directly; no conversion needed

```python
# src/domain/enums/greeting_enum.py
from enum import StrEnum

class GreetingStatus(StrEnum):
    """Represents the lifecycle status of a greeting."""
    ACTIVE = "active"
    ARCHIVED = "archived"

# src/infrastructure/database/models.py — define a shared type object at module level, reuse across models
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column

greeting_status_enum = SQLAlchemyEnum(GreetingStatus, name="greeting_status")
status: Mapped[GreetingStatus] = mapped_column(greeting_status_enum, nullable=False, default=GreetingStatus.ACTIVE)

# src/domain/entities/greeting.py — used directly on the entity
from dataclasses import field
status: GreetingStatus = field(default=GreetingStatus.ACTIVE)

# src/application/dtos/greeting_dto.py — carried through as-is
status: GreetingStatus

# src/api/schemas/greeting_schema.py — Pydantic handles StrEnum natively
status: GreetingStatus = Field(default=GreetingStatus.ACTIVE)
```

### Variable and Property Naming Conventions

**Critical Rules** — MUST be followed for all variables and properties:

1. **Collections use plural names**: `list[Greeting]` → `greetings`, single → `greeting`
2. **Sets use `_set` suffix**: `set[int]` → `greeting_id_set`
3. **Dictionaries use `_map` suffix**: `dict[int, Greeting]` → `greeting_map`
4. **Internal properties/variables prefixed with `_`** and MUST never be accessed from outside the class: `self._repository`, `self._connection_factory`, `self._engine`
5. **Meaningful and complete names — no shortforms or abbreviations**:
   - Never use single-letter or abbreviated names: `g` → `greeting`, `repo` → `repository`, `conn` → `connection`
   - Never use vague generic names: `dto` → `create_greeting_dto`, `entity` → `greeting`, `result` → `query_result`
   - When a name is already taken, name it contextually based on its role — never append numbers: `greeting1` / `greeting2` is forbidden → use `created_greeting`, `existing_greeting`, `greeting_model` etc.
6. **Booleans MUST read like questions**: `is_active`, `is_deleted`, `can_update`, `has_items` — never bare nouns (`success` → `is_successful`)

### Documentation Conventions

**Critical Rules** — MUST be followed for all docstrings:

1. **Only public methods get docstrings** — methods prefixed with `_` do NOT need docstrings
2. **Implementation methods do NOT get docstrings** — only the base class abstract method needs the docstring; the overriding implementation has none
3. **`__init__` always gets a docstring** — constructors are unique to each class, document all parameters with Args section
4. **Class-level docstrings are always required** — one-line description of purpose
5. **Methods not used outside the class MUST be prefixed with `_`**
6. **Google-style docstrings** with Args, Returns, Yields, and Raises sections as applicable

### Code Style

- **Maximum line length is 140 characters** — no line may exceed this limit
- Use `ruff` for linting and formatting (configured in `pyproject.toml`)
- After making code changes, run `ruff check src/ --fix && ruff format src/` to enforce line length and fix lint issues
- Use modern Python type annotations: `list` not `List`, `X | None` not `Optional[X]`

### Async/Await

- ALL database operations are async
- Use `async def` and `await` for DB operations

### Error Handling

```python
if greeting_dto is None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resource not found"
    )
```

## External Services (Application Layer Ports)

For external services that use cases call directly (blob storage, email, payment, etc.), the interface lives in the **application layer** — not the infrastructure layer. This keeps use cases framework-agnostic and the provider swappable with a single line change in `container.py`.

| File | Location | Purpose |
|------|----------|---------|
| `BlobStorageServiceBase` | `src/application/services/` | Interface — use cases import this |
| `BlobStorageService` | `src/infrastructure/blob_storage/` | Azure implementation |

```python
# src/application/services/blob_storage_service_base.py
class BlobStorageServiceBase(ABC):
    """Abstract base class — use cases depend only on this."""

    @abstractmethod
    async def upload(self, container_name: str, blob_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload raw bytes, returns the blob URL."""

    @abstractmethod
    async def download(self, container_name: str, blob_name: str) -> bytes: ...

    @abstractmethod
    async def delete(self, container_name: str, blob_name: str) -> bool: ...

    @abstractmethod
    async def exists(self, container_name: str, blob_name: str) -> bool: ...

# src/infrastructure/blob_storage/blob_storage_service.py
class BlobStorageService(BlobStorageServiceBase):
    """Azure Blob Storage implementation. Swap to S3BlobStorageService by changing container.py only."""

    def __init__(self, settings: Settings) -> None:
        self._client = BlobServiceClient.from_connection_string(settings.blob_storage_connection_string)

    async def upload(self, container_name: str, blob_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        async with self._client.get_blob_client(container=container_name, blob=blob_name) as blob_client:
            await blob_client.upload_blob(data, overwrite=True, content_settings=ContentSettings(content_type=content_type))
            return blob_client.url

# src/container.py — bind as singleton (shared client connection)
binder.bind(BlobStorageServiceBase, to=BlobStorageService, scope=singleton)
```

**Use in a use case:**
```python
class GreetingUseCase(GreetingUseCaseBase):
    def __init__(self, repository: GreetingRepositoryBase, blob_storage_service: BlobStorageServiceBase) -> None:
        self._repository = repository
        self._blob_storage_service = blob_storage_service
```

**To switch providers**: Create `S3BlobStorageService(BlobStorageServiceBase)` in `src/infrastructure/blob_storage/` and change `to=BlobStorageService` → `to=S3BlobStorageService` in `container.py`. The use case is untouched.

**Settings**: Add connection string to `src/config/settings.py` (loaded from env var automatically):
```python
blob_storage_connection_string: str = ""
```

---

## Multiple Repository Use Cases

Use cases with multiple repositories are resolved automatically via constructor injection:

```python
class OrderUseCase(OrderUseCaseBase):
    def __init__(
        self,
        user_repository: UserRepositoryBase,
        order_repository: OrderRepositoryBase,
    ):
        self._user_repository = user_repository
        self._order_repository = order_repository
```

## Anti-Patterns to Avoid

- **Don't pass sessions to repository constructors** — inject `ConnectionFactoryBase` instead
- **Don't use `Depends()`** — use `Injected(BaseClass)` with fastapi-injector
- **Don't bypass use cases in routes** — routes should never call repositories directly
- **Don't let Domain depend on Infrastructure** — no `from src.infrastructure...` in domain layer
- **Don't forget `Base` suffix on ABC classes** — `UserRepositoryBase`, not `UserRepository(ABC)`
- **Don't use concrete types in route signatures** — always use base classes: `Injected(UserUseCaseBase)`
- **Don't create instances manually** — let the injector resolve the dependency chain
- **Don't forget to bind in AppModule** — every new base/implementation pair needs `binder.bind()`
- **Don't forget `attach_injector(app, injector)`** — must be called before including routers
- **Don't use `singleton` for repositories/use cases** — only `ConnectionFactory` and external service clients (e.g. `BlobStorageService`) should be singleton

## Configuration

Environment variables are managed in [settings.py](src/config/settings.py) and loaded from `.env`.

Never hardcode configuration values.

## Debugging Tips

1. **Enable SQL Logging**: Set `IS_SQL_ECHO_ENABLED=true` in `.env`
2. **Check Sessions**: Ensure `async with self._connection_factory.get_session()` is used in repositories
3. **Verify DI**: Ensure `attach_injector(app, injector)` is called in main.py
4. **Check Bindings**: Verify all base classes are bound in `AppModule.configure()`
5. **Layer Violations**: Domain should never import from Infrastructure

## Database Migrations

This template uses `create_all()` for simplicity. In production, use Alembic for migrations.

## Testing Strategy

```python
# Mock the repository, not the database
@pytest.mark.asyncio
async def test_create_user():
    mock_repo = Mock(spec=UserRepositoryBase)
    use_case = UserUseCase(repository=mock_repo)
    result = await use_case.create_user(CreateUserDTO(name="John", email="john@example.com"))
    mock_repo.create.assert_called_once()
```

## File References

- [Greeting entity](src/domain/entities/greeting.py)
- [Greeting enums](src/domain/enums/greeting_enum.py)
- [Repository Base](src/domain/repositories/greeting_repository_base.py)
- [Repository implementation](src/infrastructure/repositories/greeting_repository.py)
- [DB Base](src/infrastructure/database/db.py)
- [DB models](src/infrastructure/database/models.py)
- [Connection factory Base](src/infrastructure/database/connection_factory_base.py)
- [Connection factory](src/infrastructure/database/connection_factory.py)
- [Blob storage service Base](src/application/services/blob_storage_service_base.py)
- [Blob storage service](src/infrastructure/blob_storage/blob_storage_service.py)
- [DTOs](src/application/dtos/greeting_dto.py)
- [Entity converter](src/application/converters/greeting_converter.py)
- [Use case Base](src/application/use_cases/greeting_use_case_base.py)
- [Use case implementation](src/application/use_cases/greeting_use_case.py)
- [API schemas](src/api/schemas/greeting_schema.py)
- [API converter](src/api/converters/greeting_converter.py)
- [Routes](src/api/routes/greeting_routes.py)
- [DI Container](src/container.py)
- [Settings](src/config/settings.py)
- [Main app](src/main.py)
