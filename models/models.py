<<<<<<< HEAD
# backend/models.py
from sqlalchemy import Column, Integer, String
from Core.database import Base
from Core.database import Base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timedelta


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    mot_de_passe = Column(String, nullable=False)
    role = Column(String, nullable=False)
    province = Column(String, nullable=True)
   # image = Column(String,nullable=True)
    status = Column(String, nullable=False)


class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    code = Column(String)
    expires_at = Column(DateTime, default=lambda: datetime.now() + timedelta(minutes=5))

=======
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
    image = Column(String, nullable=True)
    statuts = Column(String, nullable=False)

class PendingUser(Base):
    __tablename__ = "pending_users"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    mot_de_passe = Column(String, nullable=False)
    role = Column(String, nullable=False)
    province = Column(String, nullable=True)
    statut = Column(String, default="en attente", nullable=False)
>>>>>>> ec69cf168193bb111991e2cbcfa219cb888824b0
