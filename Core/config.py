from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi_mail import ConnectionConfig

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore les champs inconnus du .env
    )

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int  
    email_sender: str
    email_password: str
    MAIL_FROM_NAME: str = "ECAT Support"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def MAIL_CONFIG(self):
        """Retourne la configuration du mail compatible FastAPI-Mail"""
        return ConnectionConfig(
            MAIL_USERNAME=self.email_sender,
            MAIL_PASSWORD=self.email_password,
            MAIL_FROM=self.email_sender,
            MAIL_PORT=self.MAIL_PORT,
            MAIL_SERVER=self.MAIL_SERVER,
            MAIL_FROM_NAME=self.MAIL_FROM_NAME,
            MAIL_STARTTLS=True,  # <--- remplace MAIL_TLS
            MAIL_SSL_TLS=False,  # <--- remplace MAIL_SSL
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )

settings = Settings()

SECRET_KEY = "ECAT_SECRET_KEY_2025"
ALGORITHM = "HS256"
