from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas import UserCreate, UserLogin
from crud import create_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])

# Dépendance DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = create_user(db, user)
    return {"message": "Utilisateur créé avec succès", "user": db_user.email}

@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.email, credentials.mot_de_passe)
    if not user:
        raise HTTPException(status_code=400, detail="Email ou mot de passe invalide")
    return {"message": "Connexion réussie", "user": user.email, "role": user.role}
