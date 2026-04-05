from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_env: str = "dev"
    sqlite_path: str = "/app/var/app.db"
    data_root: str = "/data"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    jwt_secret: str = Field(..., min_length=32)
    access_token_minutes: int = 60 * 12
    jwt_algorithm: str = "HS256"

    lmstudio_base_url: str = "http://localhost:1234/v1"
    lmstudio_embed_model: str = ""
    lmstudio_chat_model: str = ""

    class Config:
        env_prefix = ""
        case_sensitive = False

settings = Settings()