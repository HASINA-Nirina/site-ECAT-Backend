from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi_mail import ConnectionConfig

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    DATABASE_URL: str

    email_sender: str
    email_password: str

    MAIL_FROM_NAME: str = "ECAT Support"
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.gmail.com"

    @property
    def MAIL_CONFIG(self):
        return ConnectionConfig(
            MAIL_USERNAME=self.email_sender,
            MAIL_PASSWORD=self.email_password,
            MAIL_FROM=self.email_sender,
            MAIL_PORT=465,
            MAIL_SERVER="smtp.gmail.com",
            MAIL_FROM_NAME=self.MAIL_FROM_NAME,
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=True,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True     
        )

settings = Settings()

SECRET_KEY = "ECAT_SECRET_KEY_2025"
ALGORITHM = "HS256"
