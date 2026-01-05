from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.models import User, UserLivreAccess, Antenne
from schemas.user_schemas import UserCreate,UserReadLocal,EtudiantOut
from typing import List
from fastapi import HTTPException,Depends
import jwt
from datetime import datetime, timezone, timedelta
from Core.config import SECRET_KEY, ALGORITHM
from Core.security import hash_password,verify_password
from Core.database import get_db
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

SECRET_KEY = "ECAT_SECRET_KEY_2025"
ALGORITHM = "HS256"

# Constants for repeated literals
STATUS_EN_ATTENTE = "en attente"
INVALID_CREDENTIALS_MSG = "Email ou mot de passe invalide"
ROLE_ADMIN_LOCAL = "Admin Local"


def create_user(db: Session, user: UserCreate):
    """
    Crée un utilisateur dans la table `user`.
    Pour Admin Local, le statut sera 'en attente'.
    L'antenne est déterminée à partir de la province.
    """

    # 1️⃣ Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Cet e-mail est déjà utilisé."
        )

    # 2️⃣ Hasher le mot de passe
    hashed_password = hash_password(user.mot_de_passe)

    # 3️⃣ Déterminer le statut initial selon le rôle
    role_lower = user.role.lower()
    if role_lower == "admin local":
        statut_initial = STATUS_EN_ATTENTE
    elif role_lower in ["etudiante", "admin"]:
        statut_initial = "Actif"
    else:
        statut_initial = STATUS_EN_ATTENTE

    # 4️⃣ Rechercher l'antenne correspondant à la province
    antenne = None
    if user.province:
        antenne = (
            db.query(Antenne)
            .filter(Antenne.province == user.province)
            .first()
        )

        if antenne is None:
            raise HTTPException(
                status_code=404,
                detail="Aucune antenne trouvée pour cette province."
            )

    # 5️⃣ Création de l'utilisateur
    db_user = User(
        nom=user.nom,
        prenom=user.prenom,
        email=user.email,
        mot_de_passe=hashed_password,
        province=user.province,
        role=user.role,
        statuts=statut_initial,
        antenne_id=antenne.id if antenne else None
    )

    # 6️⃣ Sauvegarde en base
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
def authenticate_user_role(email: str, password: str, db: Session):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return {"error": True, "message": INVALID_CREDENTIALS_MSG}

    try:
        password_ok = verify_password (password, user.mot_de_passe)
    except Exception:
        return {"error": True, "message": INVALID_CREDENTIALS_MSG}

    if not password_ok:
        return {"error": True, "message": INVALID_CREDENTIALS_MSG}

    #Protection spéciale : le super admin peut toujours se connecter
    if user.role.lower() == "admin":
        pass  # on ne vérifie pas le statut
    else:
        user_statut = getattr(user, "statuts", "").lower()

        if user_statut == STATUS_EN_ATTENTE:
            return {
                "error": True,
                "message": "Votre compte est en attente de validation. Veuillez contacter l'administrateur.",
                "statuts": STATUS_EN_ATTENTE
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
                "message": "Votre compte est en attente de validation. Contactez l'administrateur.",
                "statuts": user.statuts
            }
        

    #Génération du token JWT
    payload = {
        "sub": user.email,
        "role": user.role,
        "nom": user.nom,
        "prenom": user.prenom,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "error": False,
        "role": user.role,
        "token": token
    }
    

def get_all_admins_locaux(db: Session):
    admins = (
        db.query(User)
        .filter(User.role == ROLE_ADMIN_LOCAL)
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
    etudiants = db.query(User).filter(User.role == "etudiante").all()
    results = []
    for e in etudiants:
        results.append({
            "id": e.id,
            "nom": e.nom,
            "prenom": e.prenom,
            "email": e.email,
            "province": getattr(e, "province", ""),
        })
    return results
 
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
    if user.role.lower() == ROLE_ADMIN_LOCAL.lower():
        statut_initial = STATUS_EN_ATTENTE
    elif user.role.lower() in ["etudiante", "admin"]:
        statut_initial = "Actif"
    else:
        statut_initial = STATUS_EN_ATTENTE

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
        return {"error": True, "message": INVALID_CREDENTIALS_MSG}

    # Vérifier le mot de passe
    #pwd_bytes = password[:72].encode('utf-8')
    try:
        # Vérifier le mot de passe en comparant le mot de passe fourni (plain) avec le hash stocké
        password_ok = verify_password(password, user.mot_de_passe)
    except Exception:
        # en cas d'erreur de vérification (ex: hash corrompu)
        return {"error": True, "message": INVALID_CREDENTIALS_MSG}

    if not password_ok:
        return {"error": True, "message": INVALID_CREDENTIALS_MSG}

    # Vérifier le statut
    user_statut = getattr(user, "statuts", None)  #  si colonne s'appelle différemment, renvoie None
    if user_statut and user_statut.lower() == STATUS_EN_ATTENTE:
        return {"error": True, "message": "Votre compte est en attente de validation. Veuillez contacter l'administrateur.", "statuts": STATUS_EN_ATTENTE}

    if not user_statut or user_statut.lower() != "actif":
        # autre statut non autorisé
        return {"error": True, "message": f"Votre compte est '{user_statut}'. Contactez l'administrateur.", "statuts": user_statut}

    # Si tout ok -> générer token
    payload = {
        "sub": user.email,
        "role": user.role,
        "nom": user.nom,
        "prenom": user.prenom,
        "exp": datetime.now(timezone.utc) + timedelta(hours=6),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "error": False,
        "role": user.role,
        "token": token
    }


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
    admin = db.query(User).filter(User.id == admin_id, User.role==ROLE_ADMIN_LOCAL).first()

    if not admin:
        return None
    
    admin.statuts = new_status
    db.commit()
    db.refresh(admin)
    return admin
def sync_and_get_antennes(db: Session):
    """Synchronize Antenne table from distinct User.province values and return list of antennes."""
    rows = db.query(User.province).filter(User.province != None).distinct().all()
    # rows are tuples like [(province,), ...]
    provinces = [ (r[0] or "").strip().replace("\u00A0", " ") for r in rows ]

    # normalize simple variants: collapse spaces
    def normalize(s: str) -> str:
        return " ".join(s.split()).strip()

    normalized = [normalize(p) for p in provinces if p]

    created = False
    for p in normalized:
        if not db.query(Antenne).filter(Antenne.province == p).first():
            a = Antenne(province=p)
            db.add(a)
            created = True

    if created:
        db.commit()

    antennes = db.query(Antenne).filter(Antenne.actif == True).all()
    # return simple list of dicts
    return [ {"id": a.id, "province": a.province, "description": a.description, "actif": a.actif} for a in antennes ]
       

def get_stats_by_antenne(db: Session):
    """
    Retourne des statistiques agrégées par antenne.
    Format renvoyé : [{"antenne": str, "students": int, "admins": int}, ...]

    La fonction utilise la table `Antenne` si elle contient des lignes ; sinon elle dérive la liste
    des antennes depuis les valeurs distinctes dans `user.province`.
    Elle tente également de prendre en compte la colonne `user.antenne_id` si elle existe, pour
    faire des correspondances plus robustes.
    """
    # essayer de lire les antennes canonique
    antennes_rows = db.query(Antenne).all()

    provinces = []
    if antennes_rows:
        provinces = [{"id": a.id, "province": a.province} for a in antennes_rows]
    else:
        rows = db.query(User.province).filter(User.province != None).distinct().all()
        provinces = [{"id": None, "province": (r[0] or "").strip()} for r in rows if r[0]]

    results = []
    # Détecter si la colonne antenne_id existe sur le modèle User
    has_antenne_id = hasattr(User, "antenne_id")

    for p in provinces:
        prov_text = p["province"]
        if p.get("id") is not None and has_antenne_id:
            # compter students/admins soit via antenne_id soit via province (tolérance)
            students_count = db.query(User).filter(User.role == "etudiante").filter(
                or_(User.antenne_id == p["id"], User.province == prov_text)
            ).count()
            admins_count = db.query(User).filter(User.role == ROLE_ADMIN_LOCAL).filter(
                or_(User.antenne_id == p["id"], User.province == prov_text)
            ).count()
        else:
            students_count = db.query(User).filter(User.role == "etudiante", User.province == prov_text).count()
            admins_count = db.query(User).filter(User.role == ROLE_ADMIN_LOCAL, User.province == prov_text).count()

        results.append({"antenne": prov_text, "students": students_count, "admins": admins_count})

    # trier par nombre d'étudiants décroissant
    results.sort(key=lambda x: x["students"], reverse=True)
    return results
