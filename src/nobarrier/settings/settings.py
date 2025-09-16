from pydantic import BaseSettings


class Settings(BaseSettings):
    server_host: set = "0.0.0.0"
    server_port: int = 8000
    database_url: str = "sqlite:///db_first_test.sqlite3"


settings = Settings(
    _env_file=".env",
    _env_file_endcoding="utf-8"
)
