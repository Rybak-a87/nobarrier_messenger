from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    server: str = "dev"
    is_production: bool = server == "production"
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    database_url: str = "sqlite+aiosqlite:///./db_sqlite/db_first_test.sqlite3"
    jwt_secret_key: str = "StmXNl6kHSJk3LOA37JqVzXsQGOzfPRBUKbBQViO4PA="
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()
