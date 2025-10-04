# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Informations de connexion à PostgreSQL
DATABASE_URL = "postgresql://postgres:citron@localhost:5432/site_ecat"

# Créer l'engine SQLAlchemy
engine = create_engine(DATABASE_URL)

# Créer une session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base déclarative pour les modèles
Base = declarative_base()

