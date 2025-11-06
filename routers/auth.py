from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, Request
from sqlalchemy.orm import Session
from Core.database import get_db
from schemas.user_schemas import UserCreate, UserLogin
from Controllers.user_controllers import create_user, authenticate_user_role
import jwt, os, shutil
from Core.config import SECRET_KEY, ALGORITHM
from models.models import Notification, User
from dependencies import get_current_user



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
            "id": user.id,
            "nom": user.nom,
            "prenom": user.prenom,
            "role": user.role,
            "email": user.email,
            "image": image_url,
            "theme": user.theme,
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

@router.put("/me/theme")
def update_theme(
    request: Request,
    theme: str = Form(...),
    db: Session = Depends(get_db)
):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if theme not in ["light", "dark"]:
        raise HTTPException(status_code=400, detail="Thème invalide")

    user.theme = theme
    db.commit()

    return {"message": f"Thème mis à jour : {theme}"}

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
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    update_data = {}
    if prenom:
        update_data["prenom"] = prenom
    if nom:
        update_data["nom"] = nom
    if file:
        filename = f"user_{user.id}_{file.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        update_data["image"] = f"/uploads/profils/{filename}"  # Chemin correct pour fetch frontend

    if update_data:
        # Met à jour directement dans la DB
        db.query(User).filter(User.id == user.id).update(update_data)
        db.commit()

    # Récupérer les infos à jour
    updated_user = db.query(User).filter(User.id == user.id).first()
    image_url = f"http://localhost:8000{updated_user.image}" if updated_user.image else None

    return {
        "message": "Profil mis à jour avec succès",
        "user": {
            "prenom": updated_user.prenom,
            "nom": updated_user.nom,
            "image": image_url,
            "email": updated_user.email,
        },
    }


@router.post("/AdminLocalRegister")
def register_admin_local(data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        return {"error": "Cet e-mail est déjà utilisé."}

    try:
        # Créer le nouvel admin local
        new_user = create_user(db, data)

        # Initialiser le statut à "en_attente"
        new_user.statuts = "en_attente"

        #create_user
        #db.add(new_user)

        # Informer tous les super admins (role = "admin")
        super_admins = db.query(User).filter(User.role == "admin").all()
        for admin in super_admins:
            notif = Notification(
                user_id=admin.id,
                related_user_id=new_user.id,
                message=f"L'admin local {new_user.prenom} {new_user.nom} vous a envoyé une demande de creer son nouveau compte.",
                action_status="non_lu",
                type="demande_compte_admin_local"
            )
            db.add(notif)

        db.commit()
        db.refresh(new_user)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création : {str(e)}")

    return {"message": "Votre demande d’inscription est en attente de validation."}


@router.get("/notifications")
def get_notifications(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")

        notifs = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc()).all()

        return [
            {
                "id": n.id,
                "message": n.message,
                "date": n.created_at.isoformat(),  # <-- format ISO
                "action_status": n.action_status,         # <-- ajouter le status
                "type": n.type or "general",
            }
            for n in notifs
        ]

    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

    
@router.post("/notifications/{notif_id}/accepter")
def accepter_invitation(notif_id: int, db: Session = Depends(get_db), request: Request = None):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        super_admin_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

    # Vérifier que l'utilisateur est bien un super-admin
    super_admin = db.query(User).filter(User.email == super_admin_email, User.role=="admin").first()
    if not super_admin:
        raise HTTPException(status_code=403, detail="Accès refusé")

    # Récupérer la notification
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification introuvable")

    # ⚡ Mettre à jour la notification
    notif.action_status = "accepte"

    # ⚡ Activer le compte admin local correspondant
    admin_local = db.query(User).filter(User.id == notif.related_user_id).first()
    if admin_local:
        admin_local.statuts = "Actif"

    db.commit()
    return {"message": "Invitation acceptée et compte activé."}


@router.post("/notifications/{notif_id}/refuser")
def refuser_invitation(notif_id: int, db: Session = Depends(get_db), request: Request = None):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        super_admin_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

    # Vérifier que l'utilisateur est bien un super-admin
    super_admin = db.query(User).filter(User.email == super_admin_email, User.role=="admin").first()
    if not super_admin:
        raise HTTPException(status_code=403, detail="Accès refusé")

    # Récupérer la notification
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification introuvable")

    # ⚡ Mettre à jour la notification
    notif.action_status = "refuse"

    # ⚡ Bloquer le compte admin local correspondant
    admin_local = db.query(User).filter(User.id == notif.related_user_id).first()
    if admin_local:
        admin_local.statuts = "refuser"

    db.commit()
    return {"message": "Invitation refusée et compte bloqué."}


@router.put("/notifications/mark_read")
def mark_notifications_read(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Utilisateur non authentifié")

    notifs = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.action_status == "non_lu"
    ).all()

    for notif in notifs:
        notif.action_status = "lu"

    db.commit()
    return {"message": "Notifications marquées comme lues"}



