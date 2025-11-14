from typing import List
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
    AWS_ACCESS_KEY_ID: str = Field(..., env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    # AWS_SESSION_TOKEN: str = Field(..., env="AWS_SESSION_TOKEN")
    AWS_S3_BUCKET: str = Field(..., env="AWS_S3_BUCKET")
    AWS_REGION: str = Field(..., env="AWS_REGION")
    ALLOWED_ORIGIN: str = Field(..., env="ALLOWED_ORIGIN")
    FRONTEND_URL: str = Field(..., env="FRONTEND_URL")
    
    model_config = SettingsConfigDict(env_file="./app/.env", env_file_encoding="utf-8", extra="allow")

settings = Settings()