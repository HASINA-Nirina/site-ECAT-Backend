from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, Request
from sqlalchemy.orm import Session
from Core.database import get_db
from schemas.user_schemas import UserCreate, UserLogin
from Controllers.user_controllers import create_user, authenticate_user_role, create_pending_user
from models.models import User
import jwt, os, shutil
from Core.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["auth"])

UPLOAD_DIR = "uploads/profils"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/Etudiantregister")
def register_etudiant(data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        return {"error": "Cet e-mail est déjà utilisé."}

    # Création directe et active
    db_user = create_user(db, data)
    return {"message": "Compte étudiant créé avec succès", "user": db_user.email}



@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    result = authenticate_user_role(credentials.email, credentials.mot_de_passe, db)

    # Si authenticate_user_role retourne une erreur structurée
    if isinstance(result, dict) and result.get("error"):
        # On renvoie un 400 avec le message — ou 401 selon ton besoin.
        # Ici on renvoie 400 pour que le frontend lise JSON et affiche le message.
        raise HTTPException(status_code=400, detail=result.get("message"))

    # Sinon succès
    return {
        "error": False,
        "token": result["token"],
        "role": result["role"],
        "message": "Connexion réussie"
    }


@router.get("/me")
def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")

        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")

        image_url = f"http://localhost:8000{user.image}" if user.image else None

        return {
            "nom": user.nom,
            "prenom": user.prenom,
            "role": user.role,
            "email": user.email,
            "image": image_url,
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

@router.put("/me/update")
async def update_profile(
    request: Request,
    prenom: str = Form(None),
    nom: str = Form(None),
    file: UploadFile | None = None,
    db: Session = Depends(get_db),
):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Email ou mot de passe invalide")
    return {"message": "Connexion réussie", "user": user.email, "role": user.role}
