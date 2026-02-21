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
| Domain | `src/domain/` | Entities, Repository ABC (ending with `Base`), QueryRows, result enums | Nothing |
| Application | `src/application/` | Use case ABC/implementations, DTOs, Entity converters, External service ABC (ending with `Base`) | Domain only |
| Infrastructure | `src/infrastructure/` | DB models, Repository implementations | Domain, Application |
| API | `src/api/` | Routes, Request/Response schemas, API converters | Application (Base classes) |
| DI Container | `src/container.py` | DI module with `injector.Module` and `Binder.bind()` | All layers |

### File Organisation — Type + Entity Grouping

Within each layer, files are organised by **type** first, then **entity name**. Shared/cross-cutting files (enums, DB infrastructure, external services, operation schemas) stay in their own directories.

```
src/
├── domain/
│   ├── entities/
│   │   └── <entity>/                    ← one folder per entity
│   │       └── <entity>.py              # entity dataclass
│   ├── repositories/
│   │   └── <entity>/                    ← one folder per entity
│   │       ├── <entity>_repository_base.py  # repository ABC
│   │       └── <entity>_query_row.py        # query row (when needed)
│   └── enums/                           ← shared across all entities
│       ├── <entity>_enum.py
│       └── operation_results.py
│
├── application/
│   ├── use_cases/
│   │   └── <entity>/                    ← one folder per entity
│   │       ├── <entity>_dto.py
│   │       ├── <entity>_converter.py
│   │       ├── <entity>_use_case_base.py
│   │       └── <entity>_use_case.py
│   └── services/                        ← shared external service interfaces (optional)
│
├── infrastructure/
│   ├── repositories/
│   │   └── <entity>/                    ← one folder per entity
│   │       └── <entity>_repository.py
│   └── database/                        ← shared DB infrastructure
│       ├── base.py                      # DeclarativeBase
│       ├── models/                      ← one file per entity
│       │   ├── __init__.py              # re-exports all models
│       │   └── <entity>_model.py
│       ├── connection_factory_base.py
│       └── connection_factory.py
│
└── api/
    ├── routers/
    │   └── <entity>/                    ← one folder per entity
    │       ├── <entity>_schema.py
    │       ├── <entity>_converter.py
    │       └── <entity>_routes.py
    ├── schemas/                         ← shared operation response schemas
    │   └── operation_schema.py
    └── result_status_maps.py            ← shared response helpers
```

**Rule**: When adding a new entity (e.g., `Order`), create `src/domain/entities/order/`, `src/domain/repositories/order/`, `src/application/use_cases/order/`, `src/infrastructure/repositories/order/`, and `src/api/routers/order/`. Never scatter entity files into flat shared directories.

## Key Architectural Patterns

### 1. Repository Pattern with ABC Base Classes

All abstract base classes (interfaces) MUST end with `Base`.

**Critical Rule — one CRUD operation per method**: Every repository method MUST perform exactly one database operation. Never combine multiple reads, writes, or a mix of read and write in a single repository method. If a use case needs to read then write, it calls two separate repository methods in sequence. Orchestration belongs in the use case, not the repository.

```python
# CORRECT — one operation per method
async def get_by_id(self, greeting_id: int) -> Greeting | None: ...             # one SELECT
async def create(self, greeting: Greeting) -> tuple[CreateResult, int | None]: ... # one INSERT
async def delete(self, greeting_id: int) -> DeleteResult: ...                   # one DELETE

# WRONG — two operations in one method
async def delete_if_exists(self, greeting_id: int) -> DeleteResult:
    greeting = await self.get_by_id(greeting_id)   # SELECT
    if greeting:
        await self.delete(greeting_id)             # DELETE — move this orchestration to use case
```

**Mutation methods return result enums** — repositories catch all database exceptions internally and return the appropriate result enum. Use cases receive a clean result and never handle database-level exceptions.

```python
# Domain Layer - Interface (has docstrings)
class GreetingRepositoryBase(ABC):
    @abstractmethod
    async def create(self, greeting: Greeting) -> tuple[CreateResult, int | None]:
        """Persist a new greeting entity.

        Args:
            greeting: The greeting entity to persist.

        Returns:
            A tuple of (result, id). id is the newly created entity id on success, None on any failure.
        """
        pass

    @abstractmethod
    async def delete(self, greeting_id: int) -> DeleteResult:
        """Delete a greeting entity by its unique identifier.

        Args:
            greeting_id: The unique identifier of the greeting to delete.

        Returns:
            A DeleteResult enum indicating the outcome of the operation.
        """
        pass

# Infrastructure Layer - Implementation (NO docstrings on overriding methods)
class GreetingRepository(GreetingRepositoryBase):
    def __init__(self, connection_factory: ConnectionFactoryBase):
        self._connection_factory = connection_factory

    async def create(self, greeting: Greeting) -> tuple[CreateResult, int | None]:
        try:
            async with self._connection_factory.get_session() as session:
                # ... insert, flush, refresh ...
                return (CreateResult.SUCCESS, greeting_model.id)
        except IntegrityError:
            return (CreateResult.UNIQUE_CONSTRAINT_ERROR, None)
        except DBAPIError as exc:
            if isinstance(exc.__cause__, asyncpg.exceptions.DeadlockDetectedError):
                return (CreateResult.CONCURRENCY_ERROR, None)
            return (CreateResult.FAILURE, None)
        except Exception:
            return (CreateResult.FAILURE, None)

    async def delete(self, greeting_id: int) -> DeleteResult:
        try:
            async with self._connection_factory.get_session() as session:
                delete_result = await session.execute(...)
                return DeleteResult.SUCCESS if delete_result.rowcount > 0 else DeleteResult.NOT_FOUND
        except DBAPIError as exc:
            if isinstance(exc.__cause__, asyncpg.exceptions.DeadlockDetectedError):
                return DeleteResult.CONCURRENCY_ERROR
            return DeleteResult.FAILURE
        except Exception:
            return DeleteResult.FAILURE
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
        binder.bind(UserRepositoryBase, to=UserRepository)
        binder.bind(UserUseCaseBase, to=UserUseCase)

injector = Injector([AppModule()])
```

**Attach Middleware** ([main.py](src/main.py)):
```python
attach_injector(app, injector)
```

**Route Injection** ([user_routes.py](src/api/routers/user/user_routes.py)):
```python
@router.post("/users", response_model=CreateOperationResponse)
async def create_user(
    user_data: UserCreateRequest,
    use_case: UserUseCaseBase = Injected(UserUseCaseBase),
) -> JSONResponse:
    create_user_dto = UserConverter.to_create_dto(user_data)
    result, entity_id = await use_case.create_user(create_user_dto)
    return create_response(result, entity_id)
```

**Critical Rules**:
- Routes MUST use `Injected(BaseClass)` for DI (not `Depends(...)`)
- Routes MUST depend on Base classes (abstractions), never concrete implementations
- Use `singleton` scope only for shared resources (e.g., ConnectionFactory)
- The injector automatically resolves the entire dependency chain via constructor injection

## Adding New Features

When adding a new feature (e.g., "User Management"), follow this order:

#### 1. Domain Layer

```python
# src/domain/enums/user_enum.py — define any enums the entity needs
from enum import StrEnum

class UserStatus(StrEnum):
    """Represents the lifecycle status of a user."""
    ACTIVE = "active"
    SUSPENDED = "suspended"

# src/domain/entities/user/user.py
from dataclasses import field
from src.domain.enums.user_enum import UserStatus

@dataclass
class User:
    id: int | None
    name: str
    email: str
    status: UserStatus = field(default=UserStatus.ACTIVE)

# src/domain/repositories/user/user_repository_base.py
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

#### 2. Infrastructure Layer

```python
# src/infrastructure/database/models/user_model.py (new file per entity)
from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.database.base import Base

class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)

# src/infrastructure/database/models/__init__.py (add re-export after creating model)
from src.infrastructure.database.models.user_model import UserModel
__all__ = ["UserModel"]

# src/infrastructure/repositories/user/user_repository.py
class UserRepository(UserRepositoryBase):
    def __init__(self, connection_factory: ConnectionFactoryBase):
        self._connection_factory = connection_factory

    async def create(self, user: User) -> User:
        async with self._connection_factory.get_session() as session:
            # Implementation — no docstring needed (base class has it)
            pass
```

#### 3. Application Layer

```python
# src/application/use_cases/user/user_dto.py
@dataclass(frozen=True)
class CreateUserDTO:
    name: str
    email: str

@dataclass(frozen=True)
class UserDTO:
    id: int
    name: str
    email: str

# src/application/use_cases/user/user_converter.py
class UserEntityConverter:
    @staticmethod
    def to_dto(user: User) -> UserDTO:
        return UserDTO(id=user.id, name=user.name, email=user.email)

    @staticmethod
    def to_entity(create_user_dto: CreateUserDTO) -> User:
        return User(id=None, name=create_user_dto.name, email=create_user_dto.email)

# src/application/use_cases/user/user_use_case_base.py
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

# src/application/use_cases/user/user_use_case.py
class UserUseCase(UserUseCaseBase):
    def __init__(self, repository: UserRepositoryBase):
        self._repository = repository

    async def create_user(self, create_user_dto: CreateUserDTO) -> UserDTO:
        user = UserEntityConverter.to_entity(create_user_dto)
        created_user = await self._repository.create(user)
        return UserEntityConverter.to_dto(created_user)
```

#### 4. API Layer

```python
# src/api/routers/user/user_schema.py
class UserCreateRequest(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

# src/api/routers/user/user_converter.py
class UserConverter:
    @staticmethod
    def to_create_dto(request: UserCreateRequest) -> CreateUserDTO:
        return CreateUserDTO(name=request.name, email=request.email)

    @staticmethod
    def to_response(user_dto: UserDTO) -> UserResponse:
        return UserResponse(id=user_dto.id, name=user_dto.name, email=user_dto.email)

# src/api/routers/user/user_routes.py
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
from src.api.routers.user.user_routes import router as user_router
app.include_router(user_router)
```

**Note**: The injector automatically resolves the full dependency chain — no manual wiring needed.

## Important Conventions

### Class Naming Conventions

- **ABC Classes**: Must end with `Base` (e.g., `RepositoryBase`, `UseCaseBase`)
- **Entities**: Singular nouns (e.g., `User`, `Greeting`)
- **Status Enums**: Singular noun describing the concept with `StrEnum` (e.g., `GreetingStatus`, `OrderState`)
- **Operation Result Enums**: `<Operation>Result` — generic, one file per operation type, shared across all entities (e.g., `CreateResult`, `UpdateResult`, `DeleteResult`)
- **API Schemas**: `Request` for inputs, `Response` for outputs (e.g., `UserCreateRequest`, `UserResponse`)
- **DTOs**: Frozen dataclasses with `DTO` suffix (e.g., `CreateUserDTO`, `UserDTO`) — **never create a wrapper DTO class for a collection** (e.g., `UserListDTO` is forbidden); use `list[UserDTO]` directly as the return type instead
- **Use Cases**: `UserUseCaseBase` (ABC) → `UserUseCase` (implementation)

### Enum Conventions

**Critical Rules** — MUST be followed for all enums:

1. **Enums belong in the Domain layer** at `src/domain/enums/<feature>_enum.py` — they represent domain concepts and can be imported by any layer
2. **Use `StrEnum`** (Python 3.11+) — values are strings, compatible with Pydantic and SQLAlchemy without extra configuration
3. **Values are lowercase strings** matching what gets stored in the database: `ACTIVE = "active"`
4. **SQLAlchemy models** use `Enum as SQLAlchemyEnum` from `sqlalchemy` with a named type: `Column(SQLAlchemyEnum(GreetingStatus, name="greeting_status"), nullable=False)`
5. **Enums flow through all layers unchanged** — entity → DTO → API schema all use the same enum type directly; no conversion needed

```python
# src/domain/enums/user_enum.py
from enum import StrEnum

class UserStatus(StrEnum):
    """Represents the lifecycle status of a user."""
    ACTIVE = "active"
    INACTIVE = "inactive"

# src/infrastructure/database/models/<entity>_model.py — define shared type objects at module level, reuse across the model
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column

user_status_enum = SQLAlchemyEnum(UserStatus, name="user_status")
status: Mapped[UserStatus] = mapped_column(user_status_enum, nullable=False, default=UserStatus.ACTIVE)

# src/infrastructure/database/models/user_model.py — define shared type objects at module level, reuse across the model

# src/domain/entities/user/user.py — used directly on the entity
from dataclasses import field
status: UserStatus = field(default=UserStatus.ACTIVE)

# src/application/use_cases/user/user_dto.py — carried through as-is
status: UserStatus

# src/api/routers/user/user_schema.py — Pydantic handles StrEnum natively
status: UserStatus = Field(default=UserStatus.ACTIVE)
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

### DB-Generated Values

**Critical Rules** — MUST be followed for `id`, `created_at`, `updated_at`, and any other DB-generated column:

1. **`id` — never set in code**: `autoincrement=True` on the model is sufficient. Do not pass `id` to the model constructor. The entity holds `id: int | None` before insert; after `session.refresh()` it is populated from the DB.

2. **`created_at` — use `server_default=func.now()`**: The DB generates this on insert. Never set it in Python code (no `datetime.now()`, no `__post_init__`, no default in the entity). Do not pass it to the model constructor.
   ```python
   # <entity>_model.py
   from sqlalchemy import func
   created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

   # entity — no default, no __post_init__
   created_at: datetime | None = None

   # repository create() — do NOT pass created_at
   greeting_model = GreetingModel(message=greeting.message, status=greeting.status)
   await session.flush()
   await session.refresh(greeting_model)   # created_at is now populated from DB
   ```

3. **`updated_at` — use `onupdate=func.now()`**: SQLAlchemy automatically includes this column in every UPDATE statement. Never set it manually in code. It remains `None` until the first update.
   ```python
   # <entity>_model.py
   updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now(), nullable=True)

   # entity
   updated_at: datetime | None = None
   ```

4. **Always call `session.refresh()` after insert/update** to populate DB-generated values back onto the model before mapping to the entity.

### Database Constraints

**Critical Rule**: All database constraints MUST have an explicit `name` parameter. This ensures migrations (e.g., Alembic) can reference and drop constraints by name, and prevents auto-generated names that differ across environments.

This applies to every constraint type: `UniqueConstraint`, `ForeignKeyConstraint`, `CheckConstraint`, `Index`, and any other SQLAlchemy constraint.

**Always use `__table_args__`** to declare constraints — never rely on column-level shorthand (e.g., `unique=True`) for anything beyond a primary key index.

```python
from sqlalchemy import ForeignKeyConstraint, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

class OrderModel(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("reference_number", name="uq_orders_reference_number"),
        ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_orders_user_id"),
        Index("ix_orders_status", "status"),  # Index name is its first positional arg
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reference_number: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
```

**Naming convention** — use lowercase with underscores, prefixed by constraint type and table name:

| Constraint | Pattern | Example |
|---|---|---|
| Unique | `uq_{table}_{column(s)}` | `uq_users_username` |
| Foreign key | `fk_{table}_{column}` | `fk_orders_user_id` |
| Check | `ck_{table}_{description}` | `ck_orders_amount_positive` |
| Index | `ix_{table}_{column(s)}` | `ix_orders_status` |

### Async/Await

- ALL database operations are async
- Use `async def` and `await` for DB operations

### Operation Result Enums and API Responses

Use case mutations (create, update, delete) return result enums instead of raising exceptions. The three result enum types are **generic and shared across all entities** — a new entity (User, Order, etc.) uses the exact same enums without adding new files.

**Critical Rules:**
- Result enums are **generic** — `CreateResult`, `UpdateResult`, `DeleteResult`. Do NOT create entity-specific variants (e.g., `CreateGreetingResult` is wrong)
- All three result enums live together in `src/domain/enums/operation_results.py` — a single shared file
- Result enums live in the **Domain layer** and are importable by any layer
- The shared API operation response schemas live in `src/api/schemas/operation_schema.py` — import them directly in any route file
- **Repositories own all exception handling** — they catch `IntegrityError`, `DBAPIError`, and `Exception` internally and return the appropriate result enum. No exceptions propagate to the use case or API layers
- **Use cases contain no exception handling** for mutation operations — they forward the result from the repository directly
- Create use cases return `tuple[CreateResult, int | None]` — the id is `None` on failure
- Update and delete use cases return just the result enum

```python
# src/domain/enums/operation_results.py  ← all three enums, shared by ALL entities
class CreateResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    CONCURRENCY_ERROR = "concurrency_error"
    UNIQUE_CONSTRAINT_ERROR = "unique_constraint_error"

class UpdateResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    CONCURRENCY_ERROR = "concurrency_error"
    UNIQUE_CONSTRAINT_ERROR = "unique_constraint_error"
    NOT_FOUND = "not_found"

class DeleteResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    CONCURRENCY_ERROR = "concurrency_error"
    NOT_FOUND = "not_found"
```

**Use case return types — no exception handling, just forward the repository result:**
```python
# Create — repo returns (CreateResult, int | None) directly; forward as-is
async def create_greeting(self, create_greeting_dto: CreateGreetingDTO) -> tuple[CreateResult, int | None]:
    greeting = GreetingEntityConverter.to_entity(create_greeting_dto)
    return await self._repository.create(greeting)

# Delete — return repo result directly
async def delete_greeting(self, greeting_id: int) -> DeleteResult:
    return await self._repository.delete(greeting_id)
```

**Standard API operation response schemas** — shared across all entities in `src/api/schemas/operation_schema.py`:
```python
class CreateOperationResponse(BaseModel):
    result: CreateResult
    id: int | None = None          # populated only on success

class UpdateOperationResponse(BaseModel):
    result: UpdateResult

class DeleteOperationResponse(BaseModel):
    result: DeleteResult
```

**Routes call shared response helpers** from `src/api/result_status_maps.py` — each helper builds the response schema and sets the correct HTTP status code in one call:
```python
# src/api/result_status_maps.py — reusable by any entity's routes
def create_response(result: CreateResult, entity_id: int | None) -> JSONResponse: ...
def update_response(result: UpdateResult) -> JSONResponse: ...
def delete_response(result: DeleteResult) -> JSONResponse: ...

# route usage
@router.post("/greetings", response_model=CreateOperationResponse)
async def create_greeting(...) -> JSONResponse:
    result, entity_id = await use_case.create_greeting(create_greeting_dto)
    return create_response(result, entity_id)

@router.delete("/greetings/{greeting_id}", response_model=DeleteOperationResponse)
async def delete_greeting(...) -> JSONResponse:
    result = await use_case.delete_greeting(greeting_id)
    return delete_response(result)
```

**HTTP status code conventions for operation endpoints:**

| Result | HTTP Code |
|--------|-----------|
| SUCCESS (create) | 201 Created |
| SUCCESS (update/delete) | 200 OK |
| NOT_FOUND | 404 Not Found |
| UNIQUE_CONSTRAINT_ERROR | 409 Conflict |
| CONCURRENCY_ERROR | 409 Conflict |
| FAILURE | 500 Internal Server Error |

### Error Handling (Read endpoints)

```python
if greeting_dto is None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resource not found"
    )
```

## External Services (Application Layer Ports)

When a use case needs to call an external service (email, payment, etc.), the interface lives in the **application layer** — not the infrastructure layer. This keeps use cases framework-agnostic and the provider swappable with a single line change in `container.py`.

| File | Location | Purpose |
|------|----------|---------|
| `<Service>Base` | `src/application/services/` | Interface — use cases import this |
| `<Service>` | `src/infrastructure/<service>/` | Concrete implementation |

```python
# src/application/services/email_service_base.py
class EmailServiceBase(ABC):
    """Abstract base class — use cases depend only on this."""

    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> bool: ...

# src/infrastructure/email/email_service.py
class EmailService(EmailServiceBase):
    """Concrete implementation. Swap providers by changing container.py only."""

    def __init__(self, settings: Settings) -> None:
        self._client = ...  # provider-specific client

    async def send(self, to: str, subject: str, body: str) -> bool:
        ...

# src/container.py — bind as singleton (shared client connection)
binder.bind(EmailServiceBase, to=EmailService, scope=singleton)
```

**Use in a use case:**
```python
class OrderUseCase(OrderUseCaseBase):
    def __init__(self, repository: OrderRepositoryBase, email_service: EmailServiceBase) -> None:
        self._repository = repository
        self._email_service = email_service
```

**To switch providers**: Create the new implementation in `src/infrastructure/<service>/` and update `to=NewImpl` in `container.py`. The use case is untouched.

**Singleton cleanup rule**: Any singleton service that holds a long-lived resource (HTTP client, connection pool, socket) that is not automatically released must implement a `close()` method on its base class and call it in the `lifespan` shutdown block in `main.py`. The `ConnectionFactoryBase.close()` pattern is the template — follow it for every new singleton that manages external resources.

**Settings**: Add any required config to `src/config/settings.py` (loaded from env var automatically).

---

## Multiple Repository Use Cases (Non-Atomic)

When a use case calls multiple repositories but each operation is **independent** (no shared transaction needed), inject each repository directly via constructor injection — the injector resolves the full chain automatically:

```python
class OrderUseCase(OrderUseCaseBase):
    def __init__(
        self,
        user_repository: UserRepositoryBase,
        order_repository: OrderRepositoryBase,
    ) -> None:
        self._user_repository = user_repository
        self._order_repository = order_repository
```

Each repository method opens its own session. Use this when failures in one operation do not need to roll back the other.

---

## Atomic Multi-Repository Operations (`begin_transaction`)

When a use case must call multiple repository methods **atomically** — all succeed or all roll back — use `connection_factory.begin_transaction()`.

### How it works

`ConnectionFactory` maintains a `ContextVar[AsyncSession | None]` called `_active_session`. When `begin_transaction()` is entered, it opens one session, stores it in the contextvar, and yields. Every subsequent call to `get_session()` on any repository within the same async context detects the active session and reuses it instead of opening a new one. On exit, `begin_transaction()` commits (or rolls back) and resets the contextvar.

**Repositories require zero changes.** The shared session is picked up transparently.

### Session resolution in `get_session()`

```
get_session() called
       │
       ▼
_active_session set?  ──yes──▶  yield active session  (no commit — begin_transaction owns it)
       │
      no
       │
       ▼
open new session, yield, commit/rollback as normal
```

### Use case — inject `ConnectionFactoryBase` alongside repositories

```python
class OrderUseCase(OrderUseCaseBase):

    def __init__(
        self,
        connection_factory: ConnectionFactoryBase,
        user_repository: UserRepositoryBase,
        order_repository: OrderRepositoryBase,
    ) -> None:
        self._connection_factory = connection_factory
        self._user_repository = user_repository
        self._order_repository = order_repository

    async def create_order_for_user(self, user_id: int, create_order_dto: CreateOrderDTO) -> OrderDTO:
        async with self._connection_factory.begin_transaction():
            user = await self._user_repository.get_by_id(user_id)
            if user is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            order = OrderEntityConverter.to_entity(create_order_dto, user_id)
            created_order = await self._order_repository.create(order)
            return OrderEntityConverter.to_dto(created_order)
        # Both operations committed atomically here — or both rolled back on any exception
```

Non-atomic use case methods work exactly as before — omit `begin_transaction()` and each repository call manages its own session.

### No extra container bindings needed

`ConnectionFactoryBase` is already registered as a singleton. The injector resolves it automatically when declared in `__init__`.

### When to use `begin_transaction` vs plain injection

| Scenario | Pattern |
|---|---|
| Single repository, any number of methods | Inject repository only |
| Multiple repositories, independent operations | Inject repositories only |
| Multiple repositories, must all succeed or all fail | Inject `ConnectionFactoryBase` + repositories, wrap in `begin_transaction()` |
| Single repository, multiple methods that must be atomic | Inject `ConnectionFactoryBase` + repository, wrap in `begin_transaction()` |

**Critical Rule**: Do NOT use `begin_transaction` when operations are independent. Use it only when atomicity is required.

---

## Query Row Pattern

Use this pattern when a repository query returns **more data than a single domain entity holds** — for example, a JOIN across tables, an aggregation, or a projection that includes nested/computed values.

**Core idea**: The repository returns a `QueryRow` dataclass (a flat projection of the raw query result). The application converter then maps it to a DTO that the use case returns. This keeps the domain entity clean while allowing the repository to surface richer data.

### When to use it

- The query JOINs multiple tables and the result doesn't fit a single entity
- The result includes aggregated values (e.g., counts, sums)
- The result includes deeply nested or computed data that would pollute the domain entity

### Where `QueryRow` classes live

`QueryRow` classes live in `src/domain/repositories/{entity}/`, co-located with the repository base that declares them as return types. They are not entities (no lifecycle, no identity) — they are intermediate projection types that exist solely to carry the result of a specific query. Keeping them next to the repository base makes the contract self-contained and immediately discoverable.

```
src/domain/repositories/greeting/
├── greeting_repository_base.py      ← declares get_with_author() → GreetingWithAuthorQueryRow
└── greeting_query_row.py            ← defines GreetingWithAuthorQueryRow
```

### Naming and structure

```python
# src/domain/repositories/greeting/greeting_query_row.py
from dataclasses import dataclass
from datetime import datetime
from src.domain.enums.greeting_enum import GreetingStatus

@dataclass(frozen=True)
class GreetingWithAuthorQueryRow:
    id: int
    message: str
    status: GreetingStatus
    created_at: datetime
    author_name: str      # joined from users table
    reply_count: int      # aggregated from replies table
```

- Name: `{Entity}{Qualifier}QueryRow` — qualifier describes what the query adds (e.g., `WithAuthor`, `WithStats`)
- Always `frozen=True` — it is a read-only projection, never mutated
- Fields are flat — no nested objects; unfold joined data into scalar fields

### Repository base (domain layer)

```python
# src/domain/repositories/greeting/greeting_repository_base.py
@abstractmethod
async def get_with_author(self, greeting_id: int) -> GreetingWithAuthorQueryRow | None:
    """Fetch a greeting and its author details.

    Args:
        greeting_id: The unique identifier of the greeting.

    Returns:
        A GreetingWithAuthorQueryRow combining greeting and author data, or None if not found.
    """
    pass
```

### Repository implementation (infrastructure layer)

```python
# src/infrastructure/repositories/greeting/greeting_repository.py
async def get_with_author(self, greeting_id: int) -> GreetingWithAuthorQueryRow | None:
    async with self._connection_factory.get_session() as session:
        query_result = await session.execute(
            select(
                GreetingModel.id,
                GreetingModel.message,
                GreetingModel.status,
                GreetingModel.created_at,
                UserModel.name.label("author_name"),
                func.count(ReplyModel.id).label("reply_count"),
            )
            .join(UserModel, GreetingModel.author_id == UserModel.id)
            .outerjoin(ReplyModel, ReplyModel.greeting_id == GreetingModel.id)
            .where(GreetingModel.id == greeting_id)
            .group_by(GreetingModel.id, UserModel.name)
        )
        row = query_result.one_or_none()
        if row is None:
            return None
        return GreetingWithAuthorQueryRow(
            id=row.id,
            message=row.message,
            status=row.status,
            created_at=row.created_at,
            author_name=row.author_name,
            reply_count=row.reply_count,
        )
```

### DTO and converter (application layer)

Create a **dedicated DTO** for this richer result — do not reuse `GreetingDTO` if the shape differs.

```python
# src/application/use_cases/greeting/greeting_dto.py
@dataclass(frozen=True)
class GreetingWithAuthorDTO:
    id: int
    message: str
    status: GreetingStatus
    created_at: datetime
    author_name: str
    reply_count: int

# src/application/use_cases/greeting/greeting_converter.py
class GreetingEntityConverter:
    @staticmethod
    def query_row_to_dto(query_row: GreetingWithAuthorQueryRow) -> GreetingWithAuthorDTO:
        return GreetingWithAuthorDTO(
            id=query_row.id,
            message=query_row.message,
            status=query_row.status,
            created_at=query_row.created_at,
            author_name=query_row.author_name,
            reply_count=query_row.reply_count,
        )
```

### Use case

```python
async def get_greeting_with_author(self, greeting_id: int) -> GreetingWithAuthorDTO | None:
    query_row = await self._repository.get_with_author(greeting_id)
    if query_row is None:
        return None
    return GreetingEntityConverter.query_row_to_dto(query_row)
```

### Full data flow

```
Repository (infrastructure)
    ↓ returns GreetingWithAuthorQueryRow   ← flat DB projection
Application converter
    ↓ query_row_to_dto()
GreetingWithAuthorDTO                      ← typed application result
Use case
    ↓ returns GreetingWithAuthorDTO
API converter → GreetingWithAuthorResponse
```

### Critical rules

- **Never reuse the domain entity** when the query adds data the entity doesn't model — create a `QueryRow` instead
- **`QueryRow` is read-only** (`frozen=True`) — it is never passed back into the repository or mutated
- **One `QueryRow` per query shape** — if two queries return different projections, create two `QueryRow` classes
- **`QueryRow` lives in `src/domain/repositories/{entity}/`** — co-located with the repository base that declares it
- **Always convert to DTO before leaving the use case** — the API layer never receives a `QueryRow` directly

---

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
- **Don't use `singleton` for repositories/use cases** — only `ConnectionFactory` and external service clients (e.g. HTTP clients, connection pools) should be singleton
- **Don't forget to close singleton resources** — every singleton that holds an external connection (DB pool, HTTP client) must have a `close()` method on its base class and be closed in the `lifespan` shutdown block in `main.py`
- **Don't scatter entity files into flat shared directories** — follow the `src/{layer}/{type}/{entity}/` pattern

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

### Test Folder Structure

Tests live in `tests/` at the project root and mirror the `src/` source tree exactly. This keeps each test file structurally co-located with the code it exercises.

```
tests/
├── __init__.py
├── api/
│   ├── __init__.py
│   └── routers/
│       ├── __init__.py
│       └── <entity>/                          ← mirrors src/api/routers/<entity>/
│           ├── __init__.py
│           ├── test_<entity>_converter.py     # schema → DTO mapper tests
│           └── test_<entity>_routes.py        # route/endpoint tests
└── application/
    ├── __init__.py
    └── use_cases/
        ├── __init__.py
        └── <entity>/                          ← mirrors src/application/use_cases/<entity>/
            ├── __init__.py
            ├── test_<entity>_converter.py     # entity ↔ DTO mapper tests
            └── test_<entity>_use_case.py      # use case logic tests
```

**Rule**: For each entity, create parallel test folders `tests/application/use_cases/<entity>/` and `tests/api/routers/<entity>/` — one test file per source file being tested.

### What to Test (and What Not To)

| Layer | File | Test? | Reason |
|-------|------|-------|--------|
| Application | `<entity>_use_case.py` | Yes | Core business logic, mock the repository |
| Application | `<entity>_converter.py` | Yes | Entity ↔ DTO mapping correctness |
| API | `<entity>_converter.py` | Yes | Schema ↔ DTO mapping correctness |
| API | `<entity>_routes.py` | Yes | HTTP contract — status codes, request validation |
| Infrastructure | `<entity>_repository.py` | **No** | Requires a live DB; covered by integration tests |

### Running Tests

```bash
pytest                          # run all tests
pytest tests/application/       # run application-layer tests only
pytest tests/api/               # run API-layer tests only
pytest -v                       # verbose output
```

### Use Case Tests — Mock the Repository

Use `AsyncMock(spec=RepositoryBase)` to isolate business logic from the database. `asyncio_mode = "auto"` in `pyproject.toml` handles async test functions automatically — no `@pytest.mark.asyncio` decorator needed.

```python
from unittest.mock import AsyncMock
import pytest
from src.application.use_cases.user.user_use_case import UserUseCase
from src.domain.repositories.user.user_repository_base import UserRepositoryBase
from src.domain.enums.operation_results import CreateResult

@pytest.fixture
def mock_repository() -> UserRepositoryBase:
    return AsyncMock(spec=UserRepositoryBase)

@pytest.fixture
def use_case(mock_repository: UserRepositoryBase) -> UserUseCase:
    return UserUseCase(repository=mock_repository)

class TestCreateUser:
    async def test_returns_success_result_and_new_id(self, use_case: UserUseCase, mock_repository: UserRepositoryBase):
        mock_repository.create.return_value = (CreateResult.SUCCESS, 1)
        create_user_dto = CreateUserDTO(email="alice@example.com", username="alice")

        result, entity_id = await use_case.create_user(create_user_dto)

        assert result == CreateResult.SUCCESS
        assert entity_id == 1
```

**Fixture typing convention**: Annotate mock fixtures as `-> RepositoryBase` (not `-> AsyncMock`). This surfaces the repository's method names (`create`, `get_by_id`, etc.) in the IDE for all test parameters. The trade-off is that mock-specific attributes like `.return_value` and `.assert_called_once_with()` will not be type-hinted by the static analyser — they still work at runtime. `AsyncMock` remains in the import and the fixture body only as the instantiation mechanism.

### Converter Tests — Pure Unit Tests

Converter tests are synchronous and have no dependencies to mock — just construct inputs and assert outputs.

```python
from src.application.use_cases.user.user_converter import UserEntityConverter
from src.domain.entities.user.user import User

def test_to_entity_sets_id_to_none():
    create_user_dto = CreateUserDTO(email="alice@example.com", username="alice")

    user = UserEntityConverter.to_entity(create_user_dto)

    assert user.id is None
    assert user.email == "alice@example.com"
```

### Route Tests — Isolated FastAPI App with Test Injector

Routes use `fastapi_injector`'s `Injected()` for DI. To override in tests, create a fresh `FastAPI` app with a `TestModule` that binds the mock use case via `InstanceProvider`, then use `httpx.AsyncClient` with `ASGITransport`.

```python
from unittest.mock import AsyncMock
import pytest
from fastapi import FastAPI
from fastapi_injector import attach_injector
from httpx import ASGITransport, AsyncClient
from injector import Binder, Injector, InstanceProvider, Module

from src.api.routers.user.user_routes import router
from src.application.use_cases.user.user_use_case_base import UserUseCaseBase

@pytest.fixture
def mock_use_case() -> AsyncMock:
    return AsyncMock(spec=UserUseCaseBase)

@pytest.fixture
def test_app(mock_use_case: AsyncMock) -> FastAPI:
    app = FastAPI()

    class TestModule(Module):
        def configure(self, binder: Binder) -> None:
            binder.bind(UserUseCaseBase, to=InstanceProvider(mock_use_case))

    attach_injector(app, Injector([TestModule()]))
    app.include_router(router)
    return app

@pytest.fixture
async def client(test_app: FastAPI) -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as async_client:
        yield async_client

class TestCreateUserRoute:
    async def test_returns_201_with_result_and_id_on_success(self, client: AsyncClient, mock_use_case: AsyncMock):
        mock_use_case.create_user.return_value = (CreateResult.SUCCESS, 1)

        response = await client.post("/api/v1/users", json={"email": "alice@example.com", "username": "alice"})

        assert response.status_code == 201
        assert response.json()["id"] == 1
```

**Critical Rules:**
- **Never import `src/main.py` or `src/container.py` in tests** — always create a minimal `FastAPI()` app with only the router under test and a `TestModule`
- **Use `AsyncMock(spec=BaseClass)`** — the `spec` ensures mock methods match the real interface; async methods are automatically mocked as `AsyncMock`
- **Mock at the boundary nearest to the test** — use case tests mock the repository; route tests mock the use case
- **Repository tests are out of scope** — they require a live database and belong in integration tests, not unit tests
- **Group tests by method under test** using inner classes (e.g., `class TestCreateUser`, `class TestGetUser`) to keep related assertions together

## File References

**Shared infrastructure (present in every project)**
- [Operation result enums (shared)](src/domain/enums/operation_results.py)
- [Operation response schemas (shared)](src/api/schemas/operation_schema.py)
- [Response helpers and status maps (shared)](src/api/result_status_maps.py)
- [DB Base](src/infrastructure/database/base.py)
- [DB models](src/infrastructure/database/models/)
- [Connection factory Base](src/infrastructure/database/connection_factory_base.py)
- [Connection factory](src/infrastructure/database/connection_factory.py)
- [DI Container](src/container.py)
- [Settings](src/config/settings.py)
- [Main app](src/main.py)

**Per-entity file locations** (substitute `<entity>` with your entity name)

| Purpose | Path |
|---------|------|
| Entity dataclass | `src/domain/entities/<entity>/<entity>.py` |
| Entity enums | `src/domain/enums/<entity>_enum.py` |
| Repository Base | `src/domain/repositories/<entity>/<entity>_repository_base.py` |
| Repository implementation | `src/infrastructure/repositories/<entity>/<entity>_repository.py` |
| DTOs | `src/application/use_cases/<entity>/<entity>_dto.py` |
| Entity converter | `src/application/use_cases/<entity>/<entity>_converter.py` |
| Use case Base | `src/application/use_cases/<entity>/<entity>_use_case_base.py` |
| Use case implementation | `src/application/use_cases/<entity>/<entity>_use_case.py` |
| API schemas | `src/api/routers/<entity>/<entity>_schema.py` |
| API converter | `src/api/routers/<entity>/<entity>_converter.py` |
| Routes | `src/api/routers/<entity>/<entity>_routes.py` |
