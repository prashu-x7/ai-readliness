from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "App Reader"
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "app_reader"
    JWT_SECRET: str = "app_reader_super_secret_key_change_in_prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    CORS_ALLOW_ALL: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
