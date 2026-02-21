from pydantic import computed_field
from pydantic_settings import BaseSettings
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    db_driver: str = "postgresql+asyncpg"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "fastapi_db"
    is_sql_echo_enabled: bool = False
    pool_size: int = 5
    max_overflow: int = 10

    @computed_field
    @property
    def database_url(self) -> URL:
        """Build the SQLAlchemy database URL from individual connection components."""
        return URL.create(
            drivername=self.db_driver,
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )

    log_level: str = "INFO"

    blob_storage_connection_string: str = ""

    jwt_secret_key: str = "changeme-use-a-strong-random-secret-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
