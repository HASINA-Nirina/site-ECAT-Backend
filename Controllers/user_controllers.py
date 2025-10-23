from sqlalchemy.orm import Session
from models.models import User
from schemas.user_schemas import UserCreate
from passlib.hash import bcrypt
from fastapi import HTTPException



def create_user(db: Session, user: UserCreate):
    
    Hashed_password = bcrypt.hash(user.mot_de_passe[:72])
    db_user = User(
        nom=user.nom,
        prenom=user.prenom,
        email=user.email,
        mot_de_passe=Hashed_password,
        role=user.role,
        province=user.province,
        status=user.status,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user_role(email: str, password: str, db: Session):
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return {"error": "Email ou mot de passe invalide"}
    
    if user.status != "actif":
        return {"error": "Votre compte n'est pas activé. Veuillez contacter l'administrateur."}



    if not bcrypt.verify(password[:72], user.mot_de_passe):
        return {"error": "Mot de passe invalide"}

    return user.role

def new_Password(email: str, mot_de_passe: str, db:Session):
    user = db.query(User).filter(User.email == email).first()
    hashed = bcrypt.hashpw(mot_de_passe.encode('utf-8'), bcrypt.gensalt())

    user.mot_de_passe = hashed
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": True, "message2": "Mot de passe mis à jour avec succès"}

