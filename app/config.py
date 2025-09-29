from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_HOSTNAME : str = Field(..., env="DATABASE_HOSTNAME")
    DATABASE_PORT: str = Field(..., env="DATABASE_PORT")
    DATABASE_PASSWORD: str = Field(..., env="DATABASE_PASSWORD")
    DATABASE_NAME: str = Field(..., env="DATABASE_NAME")
    DATABASE_USERNAME: str = Field(..., env="DATABASE_USERNAME")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field(..., env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(..., env="ACCESS_TOKEN_EXPIRE_MINUTES")   
    GOOGLE_CLIENT_ID: str = Field(..., env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(..., env="GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = Field(..., env="GOOGLE_REDIRECT_URI")
    

    model_config = SettingsConfigDict(env_file="./app/.env", env_file_encoding="utf-8")

settings = Settings()