from pydantic_settings import BaseSettings
from urllib.parse import quote_plus
from fastapi_mail import ConnectionConfig

class Settings(BaseSettings):
    
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int  # attention int, pas str

      #email
    EMAIL_SENDER: str
    EMAIL_PASSWORD: str
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def MAIL_CONFIG(self) -> ConnectionConfig:
        """Configuration pour FastAPI-Mail"""
        return ConnectionConfig(
            MAIL_USERNAME=self.EMAIL_SENDER,
            MAIL_PASSWORD=self.EMAIL_PASSWORD,
            MAIL_FROM=self.EMAIL_SENDER,
            MAIL_PORT=self.SMTP_PORT,
            MAIL_SERVER=self.SMTP_SERVER,
            MAIL_STARTTLS=True,      
            MAIL_SSL_TLS=False,     
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()

SECRET_KEY = "ECAT_SECRET_KEY_2025"
ALGORITHM = "HS256"
