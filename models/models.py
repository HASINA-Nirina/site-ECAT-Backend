# backend/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from Core.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

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
    theme = Column(String, default="light")


    # Ajouter la relation vers Notification
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan", foreign_keys="Notification.user_id")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))  
    message = Column(String, nullable=False)           # message obligatoire
    action_status = Column(String, default="non_lu")  # non_lu / accepte / refuse
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    type = Column(String, default="general")             # info / invitation
    related_user_id = Column(Integer, ForeignKey("user.id"), nullable=True)


    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")
    related_user = relationship("User", foreign_keys=[related_user_id])  # pour accéder à l’admin local

  