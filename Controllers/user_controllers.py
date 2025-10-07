from sqlalchemy.orm import Session
from models.models import User
from schemas.user_schemas import UserCreate
from passlib.hash import bcrypt

def create_user(db: Session, user: UserCreate):
    hashed_password = bcrypt.hash(user.mot_de_passe)
    db_user = User(
        nom=user.nom,
        prenom=user.prenom,
        email=user.email,
        mot_de_passe=hashed_password,
        role=user.role,
        province=user.province
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not bcrypt.verify(password, user.mot_de_passe):
        return None
    return user
