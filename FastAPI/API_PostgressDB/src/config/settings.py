from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database settings
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_db"
    is_sql_echo_enabled: bool = False
    pool_size: int = 5
    max_overflow: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
