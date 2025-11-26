from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, Request,Response
from sqlalchemy.orm import Session
from Core.database import get_db
import jwt, os, shutil
from Controllers.user_controllers import (
    get_etudiants,
    get_all_admins_locaux,
    update_admin_status,
    get_etudiants_by_province,
    get_current_user,
    create_user,
    get_user_by_email,
    authenticate_user_role,
    modif_password,
    get_all_etudiant,
    update_user,
    verify_user_password,
    sync_and_get_antennes,
    get_stats_by_antenne,
)
from Core.config import SECRET_KEY, ALGORITHM
from models.models import Notification, User, Sujet, Antenne
from dependencies import get_current_user
from schemas.user_schemas import Province,AdminUpdateStatus, UserCreate,EtudiantOut, UserResponse,UserLogin,EmailRequest,VerifyOTPRequest,ChangePassword,EtudiantResponse,UserReadLocal,UserUpdate,PasswordVerify,UserLivreAccessCheck
from models.models import User,Sujet
from Controllers.user_controllers import get_etudiants, get_all_admins_locaux,update_admin_status, get_etudiants_by_province,get_current_user,create_user, get_user_by_email,authenticate_user_role, modif_password ,get_all_etudiant ,update_user,verify_user_password
from Controllers.Otp_controlllers import sendOtp,verify_otp
from Core.security import hash_password
from jwt.exceptions import ExpiredSignatureError
from typing import List
from fastapi import Depends


router = APIRouter(prefix="/auth", tags=["auth"])


UPLOAD_DIR = "uploads/profils"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/Etudiantregister")
def register_etudiant(data: UserCreate, db: Session = Depends(get_db)):
    # Vérification email déjà utilisé
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        return {"error": "Cet e-mail est déjà utilisé."}

    # 3. Vérifier si la province existe dans la table Antenne
    antenne_exists = db.query(Antenne).filter(Antenne.province == data.province).first() 
 

    #   Province existante (Antenne trouvée)

    # 4. Vérifier s'il existe un admin local pour cette province
    admin_local = db.query(User).filter(
        User.role == "Admin local",
        User.province == data.province
    ).first()


    if not admin_local:
        #  B.1: Pas d'admin local → notifier admin général
        super_admins = db.query(User).filter(User.role == "admin").all()
        for admin in super_admins:
            notif = Notification(
                user_id=admin.id,
                related_user_id=new_user.id,
                message=
                    f"Aucun admin local dans l'antenne « {data.province} ». "
                    f"L'étudiant {new_user.prenom} {new_user.nom} vient de créer un compte."
                ,
                action_status="non_lu",
                type="admin_local_manquant"
            )
            db.add(notif)
          # 2. Création de l'étudiant 
        try:
            new_user = create_user(db, data)
        except Exception as e:
            # Gérer les erreurs de création si nécessaire (ex: validation de mot de passe)
            print(f"Erreur lors de la création de l'utilisateur: {e}")
            return {"error": "Erreur lors de la création du compte."}

        
        db.commit() 
        db.refresh(new_user)
        return {
            "message": "Compte étudiant créé mais aucun admin local n'existe dans cette province.",
            "admin_local_missing": True,
            "user": new_user.email
        }

    # B.2: Succès complet (Admin local trouvé)
    
    # 5. Si admin local trouvé → créer notification normale
    notif = Notification(
        user_id=admin_local.id,
        related_user_id=new_user.id,
        message=f"L'étudiant {new_user.prenom} {new_user.nom} s'est inscrit dans votre province.",
        action_status="non_lu",
        type="nouvelle_inscription"
    )
    db.add(notif)
    db.commit() # Commit la notification à l'admin local

    return {
        "message": "Compte étudiant créé avec succès.",
        "user": new_user.email
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

        # Informer tous les super admins 
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



@router.post("/login")
def login(credentials: UserLogin,response: Response, db: Session = Depends(get_db)):
    result = authenticate_user_role(credentials.email, credentials.mot_de_passe, db)

    # Si authenticate_user_role retourne une erreur structurée
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    # Récupérer l'utilisateur connecté
    user = db.query(User).filter(User.email == credentials.email).first()
    if user.role == "Admin Local":
    # Trouver si un sujet pour cette province existe déjà
        titre_sujet = f"Forum – Province {user.province}"

        province_sujet = db.query(Sujet).filter(Sujet.titre == titre_sujet).first()

        # Si pas encore de sujet → on le crée
        if not province_sujet:
            province_sujet = Sujet(
                titre=titre_sujet,
                province=user.province,
                idCreateur=user.id
            )
            db.add(province_sujet)
            db.commit()
            db.refresh(province_sujet)
   

    return {
        "error": False,
        "token": result["token"],
        "role": result["role"],
        "province": user.province,
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
            "province": user.province,
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


@router.get("/GetAdminLocaux")
def list_admins_locaux(db: Session = Depends(get_db)):
    print(get_all_admins_locaux(db))
    return get_all_admins_locaux(db)

@router.put("/ChangeStatus/{admin_id}")
def change_admin_status(admin_id: int, body: AdminUpdateStatus, db: Session = Depends(get_db)):
    admin = update_admin_status(db, admin_id, body.statuts)

    if not admin:
        raise HTTPException(status_code=404, detail="Admin introuvable")

    return {"message": "Statut mis à jour"}

@router.get("/ReadEtudiantByprovince", response_model=List[EtudiantOut])
def read_etudiants(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_etudiants_by_province(current_user=current_user, db=db)


@router.get("/ReadEtudiantByprovince/{province}", response_model=List[EtudiantOut])
def read_etudiants(province: str, db: Session = Depends(get_db)):
    return get_etudiants(province =province , db=db)


@router.get("/ReadEtudiantAll", response_model=list[EtudiantResponse])
def read_etudiant(db: Session = Depends(get_db)):
    return get_all_etudiant(db)


############OTP################
@router.post("/sendOtp")
async def send_otp(data: EmailRequest , db: Session = Depends(get_db)):
    print(" Données reçues :", data)
    existing_user = db.query(User).filter(User.email == data.email).first()

    if existing_user:
        await sendOtp(data.email, db)
        return {"message": "otp envoyer"}

    print("email n existe pas ")
    return {"error":"Cet e-mail email n existe pas"}

@router.post("/verify")
def check_otp(data: VerifyOTPRequest, db: Session = Depends(get_db)):
    return  verify_otp(data.email, data.code, db)

@router.get("/ReadUser")
def read_user(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return {"id": user.id}
    
@router.post("/modifPassword")
def modif_password_endpoint(data: ChangePassword, db: Session = Depends(get_db)):
    print(f"Données reçues : id={data.id}, mot_de_passe=***")
    try:
        success = modif_password(user_id=data.id, mot_de_passe=data.mot_de_passe, db=db)
        return {"success": True, "message": "Mot de passe modifié avec succès !"}
    except Exception as e:
        print("Erreur :", e)
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/UpdateUser/{user_id}")
def modif_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    user = update_user(db, user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return {"message": "Utilisateur modifié avec succès"}


@router.post("/verifyPassword")
def verify_password_endpoint(data: PasswordVerify, db: Session = Depends(get_db)):
    # Attendu: body { id: int, mot_de_passe: str }
    user = verify_user_password(db, user_id=data.id, plain_password=data.mot_de_passe)
    if not user:
        raise HTTPException(status_code=401, detail="Mot de passe incorrect ou utilisateur introuvable")
    return {"message": "Mot de passe correct"}


@router.post("/verifyOldPassword")
def verify_password_endpoint(data: PasswordVerify, db: Session = Depends(get_db)):
    print(data)
    user = verify_user_password(db, user_id=data.id, plain_password=data.mot_de_passe)
    if not user:
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    return {"message": "Mot de passe correct"}

@router.post("/verifyPassword")
async def verify_password_endpoint(request: Request, db: Session = Depends(get_db)):
    """Vérifie le mot de passe. Accepte soit {id, mot_de_passe} soit {email, mot_de_passe}.

    Retourne 400 si le body est invalide, 401 si la vérification échoue.
    """
    data = await request.json()
    mot_de_passe = data.get("mot_de_passe")
    if not mot_de_passe:
        raise HTTPException(status_code=400, detail="Le champ 'mot_de_passe' est requis")

    if "id" in data and isinstance(data.get("id"), int):
        user = verify_user_password(db, user_id=data.get("id"), plain_password=mot_de_passe)
        if not user:
            raise HTTPException(status_code=401, detail="Mot de passe incorrect ou utilisateur introuvable")
        return {"message": "Mot de passe correct"}

    if "email" in data and isinstance(data.get("email"), str):
        email = data.get("email")
        user_obj = db.query(User).filter(User.email == email).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable pour cet email")
        user = verify_user_password(db, user_id=user_obj.id, plain_password=mot_de_passe)
        if not user:
            raise HTTPException(status_code=401, detail="Mot de passe incorrect")
        return {"message": "Mot de passe correct"}

    raise HTTPException(status_code=400, detail="Corps invalide : fournir 'id' (int) ou 'email' (str) et 'mot_de_passe'")


@router.post("/verifyOldPassword")
async def verify_old_password_endpoint(request: Request, db: Session = Depends(get_db)):
    """Compatibilité : accepte {id, mot_de_passe} ou {email, mot_de_passe}."""
    data = await request.json()
    mot_de_passe = data.get("mot_de_passe")
    if not mot_de_passe:
        raise HTTPException(status_code=400, detail="Le champ 'mot_de_passe' est requis")

    if "id" in data and isinstance(data.get("id"), int):
        user = verify_user_password(db, user_id=data.get("id"), plain_password=mot_de_passe)
        if not user:
            raise HTTPException(status_code=401, detail="Mot de passe incorrect")
        return {"message": "Mot de passe correct"}

    if "email" in data and isinstance(data.get("email"), str):
        email = data.get("email")
        user_obj = db.query(User).filter(User.email == email).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable pour cet email")
        user = verify_user_password(db, user_id=user_obj.id, plain_password=mot_de_passe)
        if not user:
            raise HTTPException(status_code=401, detail="Mot de passe incorrect")
        return {"message": "Mot de passe correct"}

    raise HTTPException(status_code=400, detail="Corps invalide : fournir 'id' (int) ou 'email' (str) et 'mot_de_passe'")

@router.post("/newPassword")
def update_password_endpoint(data: ChangePassword, db: Session = Depends(get_db)):
    print(data)
    try:
        modif_password(user_id=data.id, mot_de_passe=data.mot_de_passe, db=db)
        return {"success": True, "message": "Mot de passe modifié avec succès !"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/GetStatsByAntenne")
def stats_by_antenne(db: Session = Depends(get_db)):
    try:
        data = get_stats_by_antenne(db)
        return data
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Erreur lors du calcul des stats")
    
@router.get("/GetAdminLocaux")
def list_admins_locaux(db: Session = Depends(get_db)):
    print(get_all_admins_locaux(db))
    return get_all_admins_locaux(db)

@router.put("/ChangeStatus/{admin_id}")
def change_admin_status(admin_id: int, body: AdminUpdateStatus, db: Session = Depends(get_db)):
    admin = update_admin_status(db, admin_id, body.statuts)

    if not admin:
        raise HTTPException(status_code=404, detail="Admin introuvable")

    return {"message": "Statut mis à jour"}

@router.get("/ReadEtudiantByprovince", response_model=List[EtudiantOut])
def read_etudiants(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_etudiants_by_province(current_user=current_user, db=db)


@router.get("/ReadEtudiantByprovince/{province}", response_model=List[EtudiantOut])
def read_etudiants(province: str, db: Session = Depends(get_db)):
    return get_etudiants(province =province , db=db)


@router.get("/ReadEtudiantAll", response_model=list[EtudiantResponse])
def read_etudiant(db: Session = Depends(get_db)):
    return get_all_etudiant(db)

@router.get("/antennes")
def read_antennes(db: Session = Depends(get_db)):
    """Retourne la liste des antennes (synchronise depuis les users si nécessaire)."""
    return sync_and_get_antennes(db)


@router.get("/GetStatsByAntenne")
def get_stats_by_antenne_route(db: Session = Depends(get_db)):
    """Retourne les statistiques agrégées par antenne : students et admins.

    Cette route appelle `get_stats_by_antenne` dans les controllers et renvoie
    la liste [{antenne, students, admins}, ...].
    """
    return get_stats_by_antenne(db)
@router.post("/Etudiantregister")
def register_etudiant(data: UserCreate, db: Session = Depends(get_db)):
    # 1. Vérification email déjà utilisé (Première étape obligatoire)
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        # Retourne une erreur si l'email existe
        return {"error": "Cet e-mail est déjà utilisé."}

    # 2. Création de l'étudiant (Création unique, nécessaire pour les notifications)
    # L'étudiant est créé ici une seule fois.
    try:
        new_user = create_user(db, data)
        # Note: Si create_user n'appelle pas db.commit() lui-même, vous devrez l'ajouter ici:
        # db.commit() 
    except Exception as e:
        # Gérer les erreurs de création si nécessaire (ex: validation de mot de passe)
        print(f"Erreur lors de la création de l'utilisateur: {e}")
        return {"error": "Erreur lors de la création du compte."}


    # 3. Vérifier si la province existe dans la table Antenne
    antenne_exists = db.query(Antenne).filter(Antenne.antenne == data.province).first() 
    # REMARQUE IMPORTANTE: J'ai remplacé Antenne.province par Antenne.antenne 
    # si le nom de l'antenne est stocké dans le champ 'antenne' de la table Antenne.
    # Si le champ est bien 'province', rétablissez-le.


    if not antenne_exists:
        #  A: Province inexistante
        
        # On notifie le super admin de la province inexistante
        super_admins = db.query(User).filter(User.role == "admin_general").all()

        for admin in super_admins:
            notif = Notification(
                user_id=admin.id,
                related_user_id=new_user.id,
                message=(
                    f"Aucune antenne trouvée pour la province « {data.province} ». "
                    f"L'étudiant {new_user.prenom} {new_user.nom} s'est inscrit avec une province inexistante."
                ),
                action_status="non_lu",
                type="province_inexistante"
            )
            db.add(notif)

        db.commit() # Commit la création de l'utilisateur et les notifications

        return {
            "message": "Compte étudiant créé mais la province n'existe pas.",
            "province_error": True,
            "user": new_user.email
        }

    #  B: Province existante (Antenne trouvée)

    # 4. Vérifier s'il existe un admin local pour cette province
    admin_local = db.query(User).filter(
        User.role == "admin_local",
        User.province == data.province
    ).first()


    if not admin_local:
        #  B.1: Pas d'admin local → notifier admin général
        super_admins = db.query(User).filter(User.role == "admin_general").all()

        for admin in super_admins:
            notif = Notification(
                user_id=admin.id,
                related_user_id=new_user.id,
                message=(
                    f"Aucun admin local dans l'antenne « {data.province} ». "
                    f"L'étudiant {new_user.prenom} {new_user.nom} vient de créer un compte."
                ),
                action_status="non_lu",
                type="admin_local_manquant"
            )
            db.add(notif)
        
        db.commit() # Commit la notification aux admins généraux

        return {
            "message": "Compte étudiant créé mais aucun admin local n'existe dans cette province.",
            "admin_local_missing": True,
            "user": new_user.email
        }

    # B.2: Succès complet (Admin local trouvé)
    
    # 5. Si admin local trouvé → créer notification normale
    notif = Notification(
        user_id=admin_local.id,
        related_user_id=new_user.id,
        message=f"L'étudiant {new_user.prenom} {new_user.nom} s'est inscrit dans votre province.",
        action_status="non_lu",
        type="nouvelle_inscription"
    )
    db.add(notif)
    db.commit() # Commit la notification à l'admin local

    return {
        "message": "Compte étudiant créé avec succès.",
        "user": new_user.email
    }
