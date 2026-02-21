# FastAPI Clean Architecture Template

A production-ready FastAPI application template built with Clean Architecture principles, async SQLAlchemy, and dependency injection.

## Get This Template

Navigate to your target directory first, then run the appropriate command for your OS:

**macOS / Linux**
```bash
curl -fsSL https://github.com/joe-vi/Templates/archive/refs/heads/main.tar.gz | tar -xz --strip-components=3 "Templates-main/FastAPI/API_PostgressDB"
```

**Windows (PowerShell)**
```powershell
Invoke-WebRequest -Uri "https://github.com/joe-vi/Templates/archive/refs/heads/main.zip" -OutFile t.zip; Expand-Archive t.zip .; Move-Item "Templates-main/FastAPI/API_PostgressDB/*" .; Remove-Item Templates-main,t.zip -Recurse
```

## Features

- **Clean Architecture**: Separation of concerns with distinct layers (Domain, Application, Infrastructure, API)
- **Async Database**: Asynchronous PostgreSQL operations using SQLAlchemy 2.0+ and asyncpg
- **Dependency Injection**: Automatic DI with `fastapi-injector` using `Injected[Type]` annotations
- **ConnectionFactory**: Async context manager for database session management with singleton scope
- **Type Safety**: Full type hints with ABC base classes for all abstractions
- **Constructor Injection**: Dependencies automatically injected via constructors
- **Package Management**: Modern Python package management with `uv`

## Project Structure

```
.
├── src/
│   ├── domain/                 # Business entities and repository interfaces
│   │   ├── entities/
│   │   │   └── greeting.py
│   │   └── repositories/
│   │       └── greeting_repository_base.py
│   ├── application/            # Business logic and use cases
│   │   ├── schemas/
│   │   │   └── greeting_schema.py
│   │   └── use_cases/
│   │       ├── greeting_use_case_base.py
│   │       └── greeting_use_case.py
│   ├── infrastructure/         # External services and implementations
│   │   ├── database/
│   │   │   ├── config.py
│   │   │   ├── connection_factory.py
│   │   │   └── models.py
│   │   └── repositories/
│   │       └── greeting_repository.py
│   ├── api/                    # API layer
│   │   ├── dependencies.py
│   │   └── routes/
│   │       └── greeting_routes.py
│   ├── container.py            # DI container with bindings
│   └── main.py                 # FastAPI application
├── pyproject.toml
├── .env.example
└── README.md
```

## Clean Architecture Layers

### 1. Domain Layer
- **Entities**: Core business objects (`greeting.py`)
- **Repository Interfaces**: Abstract base classes ending with `Base` (`GreetingRepositoryBase`)
- **Rules**: No dependencies on outer layers

### 2. Application Layer
- **Use Cases**: Business logic operations with base classes (`GreetingUseCaseBase`, `GreetingUseCase`)
- **Schemas**: Request/Response DTOs using Pydantic
- **Rules**: Depends only on Domain layer. All use cases have Base abstractions.

### 3. Infrastructure Layer
- **Database**: ConnectionFactory for async session management
- **Repository Implementations**: Concrete implementations of repository interfaces
- **External Services**: Third-party integrations
- **Rules**: Implements interfaces from Domain layer

### 4. API Layer
- **Routes**: FastAPI endpoints
- **Dependencies**: Dependency injection setup
- **Main**: Application entry point
- **Rules**: Depends on Application layer through DI

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Clone the repository

2. Install uv (if not already installed):

**macOS / Linux**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell)**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. Install dependencies (creates the virtual environment automatically):
```bash
uv sync
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. Ensure PostgreSQL is running and create the database:
```bash
createdb fastapi_db
```

## Running the Application

### 1. Start the Database

The project includes a `docker-compose.yml` to run PostgreSQL 18:

```bash
docker compose up -d
```

To stop the database:

```bash
docker compose down
```

To stop and delete the database volume:

```bash
docker compose down -v
```

### 2. Start the Application

#### Option A: VS Code (Recommended)

A `.vscode/launch.json` is included for one-click debugging. Press `F5` or open the **Run and Debug** panel and select **FastAPI**.

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "src.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ],
            "envFile": "${workspaceFolder}/.env",
            "jinja": true
        }
    ]
}
```

#### Option B: Command Line

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- Main API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Hello World
```bash
GET /api/v1/hello
```

Response:
```json
{
  "message": "Hello, World!",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### Create Greeting
```bash
POST /api/v1/greetings
Content-Type: application/json

{
  "message": "Welcome to Clean Architecture!"
}
```

### Get Greeting by ID
```bash
GET /api/v1/greetings/{greeting_id}
```

### Get All Greetings
```bash
GET /api/v1/greetings
```

### Delete Greeting
```bash
DELETE /api/v1/greetings/{greeting_id}
```

## Database Session Management

The application uses `ConnectionFactory` injected into repositories for session management.

### Repository Pattern with ConnectionFactory

Repositories receive `ConnectionFactoryBase` via dependency injection and manage their own sessions:

```python
class GreetingRepository(GreetingRepositoryBase):
    def __init__(self, connection_factory: ConnectionFactoryBase):
        self.connection_factory = connection_factory

    async def get_by_id(self, greeting_id: int) -> Optional[Greeting]:
        async with self.connection_factory.get_session() as session:
            # Session is automatically created
            result = await session.execute(...)
            # Session is automatically committed and closed
            return result
```

Benefits:
- Repositories manage their own session lifecycle
- Automatic transaction handling with auto-commit/rollback
- Connection pooling
- Resource cleanup
- Better separation of concerns (session management within repository layer)

## Dependency Injection

This application uses `fastapi-injector` which integrates the `injector` library with FastAPI middleware for automatic dependency injection.

### AppModule Setup

The DI module uses `Binder.bind()` to map abstract base classes to their concrete implementations:

```python
# src/container.py
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

### Attach Injector Middleware

Attach the injector to the FastAPI app to enable automatic dependency injection:

```python
# src/main.py
from fastapi import FastAPI
from fastapi_injector import attach_injector
from src.container import injector

app = FastAPI(...)

# Attach injector as middleware - enables Injected[Type] in routes
attach_injector(app, injector)
```

### Using Dependencies in Routes

Routes use `Injected[Type]` for automatic dependency injection:

```python
# src/api/routes/greeting_routes.py
from fastapi_injector import Injected
from src.application.use_cases.greeting_use_case_base import GreetingUseCaseBase

@router.post("/greetings", status_code=status.HTTP_201_CREATED)
async def create_greeting(
    greeting_data: GreetingCreateSchema,
    use_case: Injected[GreetingUseCaseBase],  # Automatic injection!
) -> GreetingResponseSchema:
    greeting = await use_case.create_greeting(greeting_data.message)
    return GreetingResponseSchema(
        id=greeting.id,
        message=greeting.message,
        created_at=greeting.created_at,
    )
```

**How it works:**
1. `Injected[GreetingUseCaseBase]` requests the use case
2. Injector resolves `GreetingUseCaseBase` to `GreetingUseCase`
3. Injector creates `GreetingUseCase` and injects `GreetingRepositoryBase` via constructor
4. Injector resolves `GreetingRepositoryBase` to `GreetingRepository`
5. Injector creates `GreetingRepository` and injects `ConnectionFactoryBase` (singleton) via constructor
6. Entire dependency chain resolved automatically!

Benefits:
- **Zero boilerplate**: No manual dependency functions needed
- **Loose coupling**: Routes depend on abstractions, not implementations
- **Constructor injection**: Dependencies injected via constructors
- **Easy testing**: Mock base classes instead of concrete types
- **Flexibility**: Change implementations without modifying routes
- **Automatic resolution**: Injector handles the entire dependency graph
- **Singleton support**: ConnectionFactory shared across all requests

## Development

### Running Tests
```bash
uv run pytest
```

### Code Formatting
```bash
uv run ruff format src/
```

### Linting
```bash
uv run ruff check src/
```

### Type Checking
```bash
uv run mypy src/
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_db |
| ECHO_SQL | Log SQL queries | false |
| POOL_SIZE | Connection pool size | 5 |
| MAX_OVERFLOW | Max overflow connections | 10 |

## Design Principles

1. **Dependency Inversion**: High-level modules don't depend on low-level modules
2. **Single Responsibility**: Each class has one reason to change
3. **Open/Closed**: Open for extension, closed for modification
4. **Interface Segregation**: All ABC classes end with `Base`
5. **Async/Await**: Full async support for database operations

## Adding New Features

1. Create entity in `domain/entities/`
2. Create repository interface in `domain/repositories/` (ending with `Base`)
3. Create repository implementation in `infrastructure/repositories/` (inject `ConnectionFactoryBase` in constructor)
4. Create use case interface in `application/use_cases/` (ending with `Base`)
5. Create use case implementation in `application/use_cases/` (inject repository in constructor)
6. Create schemas in `application/schemas/`
7. Add bindings to `AppModule` in `container.py`:
   ```python
   binder.bind(NewRepositoryBase, to=NewRepository)  # Request scope
   binder.bind(NewUseCaseBase, to=NewUseCase)        # Request scope
   ```
8. Create routes in `api/routes/` using `Injected[BaseClass]`:
   ```python
   from fastapi_injector import Injected

   @router.post("/items")
   async def create_item(
       use_case: Injected[ItemUseCaseBase],  # Automatic injection!
   ) -> ItemResponseSchema:
       ...
   ```
9. Register routes in `main.py` (after `attach_injector()`)

**Note**: No manual dependency functions needed! The injector automatically resolves the entire dependency chain through constructor injection.

## License

MIT License
