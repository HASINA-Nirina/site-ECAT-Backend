# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from Core.config import Settings

SQLALCHEMY_DATABASE_URL = Settings.DATABASE_URL
# Créer l'engine SQLAlchemy

engine = create_engine(SQLALCHEMY_DATABASE_URL,pool_pre_ping=True)
engine.dispose()
# Créer une session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base déclarative pour les modèles
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally :
        db.close()