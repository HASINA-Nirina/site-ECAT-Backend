from sqlalchemy.orm import Session
from models.models import User
from schemas.user_schemas import UserCreate
from passlib.hash import bcrypt
from fastapi import HTTPException
import jwt
import datetime
from Core.config import SECRET_KEY, ALGORITHM

SECRET_KEY = "ECAT_SECRET_KEY_2025"
ALGORITHM = "HS256"


def create_user(db: Session, user: UserCreate):
    """
    Crée un utilisateur dans la table `user`.
    Pour Admin Local, le statut sera 'en attente'.
    """
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Cet e-mail est déjà utilisé.")

    hashed_password = bcrypt.hash(user.mot_de_passe)

    role_lower = user.role.lower()
    if role_lower == "admin local":
        statut_initial = "en attente"
    elif role_lower in ["etudiante", "admin"]:
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
        return {"error": True, "message": "Email ou mot de passe invalide"}

    try:
        password_ok = bcrypt.verify(password, user.mot_de_passe)
    except Exception:
        return {"error": True, "message": "Email ou mot de passe invalide"}

    if not password_ok:
        return {"error": True, "message": "Email ou mot de passe invalide"}

    #Protection spéciale : le super admin peut toujours se connecter
    if user.role.lower() == "admin":
        pass  # on ne vérifie pas le statut
    else:
        user_statut = getattr(user, "statuts", "").lower()

        if user_statut == "en attente":
            return {
                "error": True,
                "message": "Votre compte est en attente de validation. Veuillez contacter l'administrateur.",
                "statuts": "en attente"
            }

        if user_statut == "refuser" or user_statut == "refusé":
            return {
                "error": True,
                "message": "Votre compte a été refusé par l’administrateur. Vous ne pouvez pas vous connecter.",
                "statuts": user.statuts
            }

        if user_statut != "actif":
            return {
                "error": True,
                "message": f"Votre compte est en attente de validation. Contactez l'administrateur.",
                "statuts": user.statuts
            }
        
         # Durée plus longue pour le super-admin
        if user.role.lower() == "admin":
            expire_hours = 24  # ou 48h selon mon besoin
        else:
            expire_hours = 9   # durée normale pour autres utilisateurs

    #Génération du token JWT
    payload = {
        "sub": user.email,
        "role": user.role,
        "nom": user.nom,
        "prenom": user.prenom,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "error": False,
        "role": user.role,
        "token": token
    }
