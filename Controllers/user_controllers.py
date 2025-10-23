from sqlalchemy.orm import Session
from models.models import User, PendingUser
from schemas.user_schemas import UserCreate
from passlib.hash import bcrypt
from fastapi import HTTPException
import jwt
import datetime
from Core.config import SECRET_KEY, ALGORITHM


# 🔐 Clé secrète — à mettre dans un fichier .env si possible
SECRET_KEY = "ECAT_SECRET_KEY_2025"
ALGORITHM = "HS256"


def create_user(db: Session, user: UserCreate):
    """
    Crée un utilisateur dans la table `user`.
    Pour Admin Local, le statut sera 'en attente'.
    """
    pwd_bytes = user.mot_de_passe[:72].encode('utf-8')
    hashed_password = bcrypt.hash(pwd_bytes)

    # Déterminer le statut selon le rôle
    if user.role.lower() == "Admin Local":
        statut_initial = "en attente"
    elif user.role.lower() in ["etudiante", "admin"]:
        statut_initial = "Actif"
    else:
        statut_initial = "en attente"

    db_user = User(
        nom=user.nom,
        prenom=user.prenom,
        email=user.email,
        mot_de_passe=hashed_password,
        province=user.province,
        role=user.role,
        statuts=statut_initial
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user




def authenticate_user_role(email: str, password: str, db: Session):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Pas d'utilisateur → erreur classique
        return {"error": True, "message": "Email ou mot de passe invalide"}

    # Vérifier le mot de passe
    pwd_bytes = password[:72].encode('utf-8')
    try:
        password_ok = bcrypt.verify(pwd_bytes, user.mot_de_passe)
    except Exception:
        # en cas d'erreur de vérification
        return {"error": True, "message": "Email ou mot de passe invalide"}

    if not password_ok:
        return {"error": True, "message": "Email ou mot de passe invalide"}

    # Vérifier le statut (attention : nom de colonne = statuts dans ta DB)
    user_statut = getattr(user, "statuts", None)  # safe : si colonne s'appelle différemment, renvoie None
    if user_statut == "en attente":
        return {"error": True, "message": "Votre compte est en attente de validation. Veuillez contacter l'administrateur.", "statuts": "en attente"}

    if user_statut != "Actif":
        # autre statut non autorisé
        return {"error": True, "message": f"Votre compte est '{user_statut}'. Contactez l'administrateur.", "statuts": user_statut}

    # Si tout ok -> générer token
    payload = {
        "sub": user.email,
        "role": user.role,
        "nom": user.nom,
        "prenom": user.prenom,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=6),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "error": False,
        "role": user.role,
        "token": token
    }

def create_pending_user(db: Session, user: UserCreate):
    """
    Crée un compte en attente de validation (Admin Local)
    """
    existing_pending = db.query(PendingUser).filter(PendingUser.email == user.email).first()
    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user or existing_pending:
        return {"error": "Cet e-mail est déjà utilisé."}

    pwd_bytes = user.mot_de_passe[:72].encode('utf-8')
    hashed_password = bcrypt.hash(pwd_bytes)

    pending_user = PendingUser(
        nom=user.nom,
        prenom=user.prenom,
        email=user.email,
        mot_de_passe=hashed_password,
        province=user.province,
        role=user.role,
        statut="en attente"
    )

    db.add(pending_user)
    db.commit()
    db.refresh(pending_user)
    return {"message": "Demande d’inscription en attente", "email": pending_user.email}