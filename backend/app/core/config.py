from typing import Optional
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "GovSmart API"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = "supersecretkeygovsmart2026!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    MYSQL_USER: str = "govsmart_user"
    MYSQL_PASSWORD: str = "govsmart_password"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: str = "3306"
    MYSQL_DB: str = "govsmart"
    DATABASE_URL: Optional[str] = None
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
