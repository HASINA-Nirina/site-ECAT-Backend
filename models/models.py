from sqlalchemy import Column, Integer, String
from Core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey ,Enum ,Boolean
from schemas.user_schemas import PaymentStatus
from datetime import datetime, timedelta
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from Core.security import hash_password 

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    mot_de_passe = Column(String, nullable=False)
    role = Column(String, nullable=False)
    province = Column(String, nullable=True)
    antenne_id = Column(Integer, ForeignKey("antenne.id"), nullable=True)
    image = Column(String, nullable=True)
    statuts = Column(String, nullable=False)

    paiements = relationship("Paiement", back_populates="utilisateur")
    antenne = relationship("Antenne", back_populates="users")

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


class Antenne(Base):
    __tablename__ = "antenne"

    id = Column(Integer, primary_key=True, index=True)
    province = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return f"<Antenne id={self.id} province={self.province}>"

    # relation to users
    users = relationship("User", back_populates="antenne")

class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    code = Column(String)
    expires_at = Column(DateTime, default=lambda: datetime.now() + timedelta(minutes=5))

class Formation(Base):
    __tablename__ = "formation"

    idFormation = Column(Integer, primary_key=True, index=True)
    titre = Column(String,nullable=False)
    description = Column(String, nullable=False)
    date_creation = Column(DateTime, default=datetime.now(timezone.utc))
    image = Column(String, nullable=True)

    livre = relationship("Livre", back_populates="Formation")

class Livre(Base):
    __tablename__ = "livre"

    idLivre = Column(Integer, primary_key=True, index=True)
    idFormation = Column(Integer, ForeignKey("formation.idFormation"), nullable=False)
    titre = Column(String,nullable=False)
    auteur = Column(String, nullable=True)
    urlPdf = Column(String, nullable=False)
    image = Column(String, nullable=True)
    prix = Column(Float,nullable=False)
    description = Column(String,nullable=True)
    

    paiements = relationship("Paiement", back_populates="livre")
    
    Formation = relationship("Formation", back_populates="livre")
class UserLivreAccess(Base):
    __tablename__ = "user_livre_access"

    id = Column(Integer, primary_key=True, index=True)
    idUser = Column(Integer, ForeignKey("user.id"))
    idLivre = Column(Integer, ForeignKey("livre.idLivre"))
    canAccess = Column(Boolean, default=True)


class Paiement(Base):
    __tablename__ = "paiement"

    idPaiement = Column(Integer, primary_key=True, index=True)

    idUtilisateur = Column(Integer, ForeignKey("user.id"), nullable=False)
    idLivre = Column(Integer, ForeignKey("livre.idLivre"), nullable=False)
    contact = Column(Integer, nullable=False)
    montant = Column(Float, nullable=False)
    operateur = Column(String, nullable=False)
    reference = Column(String, nullable=False, unique=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    date_creation = Column(DateTime, default=datetime.now(timezone.utc))
    date_mise_a_jour = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    utilisateur = relationship("User", back_populates="paiements")
    livre = relationship("Livre", back_populates="paiements")


class Sujet(Base):
    __tablename__ = "sujet"

    idSujet = Column(Integer, primary_key=True, index=True)
    titre = Column(String, nullable=False)
    idCreateur = Column(Integer, ForeignKey("user.id"), nullable=False)
    date_creation = Column(DateTime, default=datetime.now(timezone.utc))

    # Relation vers les messages
    messages = relationship("Message", back_populates="sujet")


class Message(Base):
    __tablename__ = "message"

    idMessage = Column(Integer, primary_key=True, index=True)
    idSender = Column(Integer, ForeignKey("user.id"), nullable=False)
    idSujet = Column(Integer, ForeignKey("sujet.idSujet"), nullable=False)
    contenu = Column(String, nullable=False)
    date_creation = Column(DateTime, default=datetime.now(timezone.utc))
    idParentMessage = Column(Integer, ForeignKey("message.idMessage"), nullable=True)  # pour réponses imbriquées

    # Relations
    sujet = relationship("Sujet", back_populates="messages")
    parent = relationship("Message", remote_side=[idMessage], backref="reponses")
