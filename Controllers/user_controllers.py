from sqlalchemy.orm import Session
from models.models import User
from schemas.user_schemas import UserCreate
from passlib.hash import bcrypt
from fastapi import HTTPException
import jwt
import datetime

# 🔐 Clé secrète — à mettre dans un fichier .env si possible
SECRET_KEY = "votre_cle_secrete_ultra_longue"
ALGORITHM = "HS256"

def create_user(db: Session, user: UserCreate):
    # Limiter à 72 caractères et encoder en bytes pour bcrypt
    pwd_bytes = user.mot_de_passe[:72].encode('utf-8')
    hashed_password = bcrypt.hash(pwd_bytes)

    db_user = User(
        nom=user.nom,
        prenom=user.prenom,
        email=user.email,
        mot_de_passe=hashed_password,
        province=user.province,
        role=user.role,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user_role(email: str, password: str, db: Session):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe invalide")

    # Vérifier le mot de passe
    pwd_bytes = password[:72].encode('utf-8')
    if not bcrypt.verify(pwd_bytes, user.mot_de_passe):
        raise HTTPException(status_code=401, detail="Email ou mot de passe invalide")

    # ✅ Créer un token JWT
    payload = {
        "sub": user.email,
        "role": user.role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=6),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # ✅ Retourne le rôle et le token
    return {
        "role": user.role,
        "token": token
    }
