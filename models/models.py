# backend/models.py
from sqlalchemy import Column, Integer, String
from Core.database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    mot_de_passe = Column(String, nullable=False)
    role = Column(String, nullable=False)
    province = Column(String, nullable=True)
