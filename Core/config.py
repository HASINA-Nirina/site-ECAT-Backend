<<<<<<< HEAD
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int  # attention int, pas str

    EMAIL_SENDER: str
    EMAIL_PASSWORD: str
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()  # note le nom en minuscule pour éviter le conflit

SECRET_KEY = "ECAT_SECRET_KEY_2025"
ALGORITHM = "HS256"
=======
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int  # attention int, pas str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()  # note le nom en minuscule pour éviter le conflit

SECRET_KEY = "ECAT_SECRET_KEY_2025"
ALGORITHM = "HS256"

>>>>>>> ec69cf168193bb111991e2cbcfa219cb888824b0
