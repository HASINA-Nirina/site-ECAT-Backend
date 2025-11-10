from sqlalchemy.orm import Session
from models.models import User, PendingUser, UserLivreAccess
from schemas.user_schemas import UserCreate,UserReadLocal,EtudiantOut
from typing import List
import bcrypt
from passlib.hash import bcrypt
from fastapi import HTTPException,Depends
import jwt
import datetime
from Core.config import SECRET_KEY, ALGORITHM
from Core.security import hash_password,verify_password
from Core.database import get_db
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError 



SECRET_KEY = "ECAT_SECRET_KEY_2025"
ALGORITHM = "HS256"


def get_all_admins_locaux(db: Session):
    admins = (
        db.query(User)
        .filter(User.role == "Admin Local")
        .all()
    )

    results = []
    for a in admins:
        # Count students in same antenne (province)
        students_count = (
            db.query(User)
            .filter(User.role == "etudiante", User.province == a.province)
            .count()
        )

        results.append({
            "id": a.id,
            "nom": a.nom,
            "prenom": a.prenom,
            "email": a.email,
            "antenne": a.province,
            "etudiants": students_count,
            "statut": a.statuts,  
            "avatar": a.image
        })

    return results

def update_user(db: Session, user_id: int, data):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    user.nom = data.nom
    user.prenom = data.prenom
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(email: str, db: Session):
    """
    Récupère un utilisateur dans la DB via son email
    """
    return db.query(User).filter(User.email == email).first()

def get_all_etudiant(db: Session):
    return db.query(User).filter(User.role == "etudiant").all()
 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token invalide")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    return user
  

def get_etudiants_by_province(current_user=Depends(get_current_user), db: Session = Depends(get_db)) -> List[EtudiantOut]:
    if not current_user:
        raise HTTPException(status_code=401, detail="Utilisateur non authentifié")
    
    etudiants = db.query(User).filter(User.province == current_user.province,User.role == "etudiante").all()
    return [
        EtudiantOut(
            id=e.id,
            nom=e.nom,
            prenom=e.prenom,
            email=e.email,

        
        )
        for e in etudiants
    ]
def get_etudiants(province:str, db: Session = Depends(get_db)) -> List[EtudiantOut]: 
    etudiants = db.query(User).filter(User.province == province,User.role == "etudiante").all()
    return [
        EtudiantOut(
            id=e.id,
            nom=e.nom,
            prenom=e.prenom,
            email=e.email,
            
        
        )
        for e in etudiants
    ]

def create_user(db: Session, user: UserCreate):
    """
    Crée un utilisateur dans la table `user`.
    Pour Admin Local, le statut sera 'en attente'.
    """
   
    hashed_password = hash_password(user.mot_de_passe)

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
    #pwd_bytes = password[:72].encode('utf-8')
    try:
       # password_ok = bcrypt.verify(pwd_bytes, user.mot_de_passe)
       password_ok=hash_password(user.mot_de_passe)
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

   # pwd_bytes = user.mot_de_passe[:72].encode('utf-8')
    hashed_password = hash_password(user.mot_de_passe)
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

def verify_user_password(db: Session, user_id: int, plain_password: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    if verify_password(plain_password, user.mot_de_passe):
        return user
    return None


def modif_password(user_id: int, mot_de_passe: str, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    user.mot_de_passe = hash_password(mot_de_passe)
    db.commit()
    return {"success": True}

def update_admin_status(db: Session, admin_id: int, new_status: str):
    admin = db.query(User).filter(User.id == admin_id, User.role=="Admin Local").first()

    if not admin:
        return None
    
    admin.statuts = new_status
    db.commit()
    db.refresh(admin)
    return admin
       



