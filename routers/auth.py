from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Core.database import get_db
from schemas.user_schemas import UserCreate, UserLogin
from Controllers.user_controllers import create_user, authenticate_user_role
from models.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/Etudiantregister")
def register(data: UserCreate, db: Session = Depends(get_db)):
    # Vérifier si l'email existe déjà
    print("Verification")
    existing_user = db.query(User).filter(User.email == data.email).first()

    if existing_user:
        # Retourne une erreur HTTP 400 avec un message explicite
        print("email deja utilise")
        return {"error":"Cet e-mail est déjà utilisé."}

    # Si tout va bien, créer l'utilisateur
    db_user = create_user(db, data)
    return {"message": "Utilisateur créé avec succès", "user": db_user.email}

@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    print("Données reçues :", credentials)
    result = authenticate_user_role(credentials.email, credentials.mot_de_passe, db)
    print("Résultat de l'authentification :", result)

    # Cas d'erreur (email ou mot de passe invalide)
    if isinstance(result, dict) and "error" in result:
        return {"error": True, "message": result["error"]}

    # Cas succès → doit renvoyer toujours un objet avec token + role
    return {
        "error": False,
        "token": result["token"],  # JWT retourné depuis la fonction
        "role": result["role"],
        "message": "Connexion réussie"
    }
