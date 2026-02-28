from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"
    sqlite_path: str = "/app/var/app.db"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    jwt_secret: str = "change-me"

    class Config:
        env_prefix = ""
        case_sensitive = False

settings = Settings()