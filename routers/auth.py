from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, Request,Response
from sqlalchemy.orm import Session
from Core.database import get_db
from schemas.user_schemas import Province,AdminUpdateStatus, UserCreate,EtudiantOut, UserResponse,UserLogin,EmailRequest,VerifyOTPRequest,ChangePassword,EtudiantResponse,UserReadLocal,UserUpdate,PasswordVerify,UserLivreAccessCheck
from models.models import User,Sujet
from Controllers.user_controllers import get_etudiants, get_all_admins_locaux,update_admin_status, get_etudiants_by_province,get_current_user,create_user, get_user_by_email,authenticate_user_role, modif_password ,get_all_etudiant ,update_user,verify_user_password
from Controllers.Otp_controlllers import sendOtp,verify_otp
import jwt, os, shutil
from Core.security import hash_password
from Core.config import SECRET_KEY, ALGORITHM
import jwt
from jwt.exceptions import ExpiredSignatureError
from typing import List
from fastapi import Depends


router = APIRouter(prefix="/auth", tags=["auth"])

UPLOAD_DIR = "uploads/profils"
os.makedirs(UPLOAD_DIR, exist_ok=True)


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

@router.post("/Etudiantregister")
def register_etudiant(data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        return {"error": "Cet e-mail est déjà utilisé."}

    # Création directe et active
    db_user = create_user(db, data)
    return {"message": "Compte étudiant créé avec succès", "user": db_user.email}

@router.post("/AdminLocalRegister")
def register_admin_local(data: UserCreate, db: Session = Depends(get_db)):
    # Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        return {"error": "Cet e-mail est déjà utilisé."}

    try:
        # Créer le nouvel admin local
        new_user = create_user(db, data)

        # Informer tous les super admins (role = "admin")
        super_admins = db.query(User).filter(User.role == "admin").all()
        for admin in super_admins:
            notif = Notification(
                user_id=admin.id,
                message=f"L'admin local {new_user.prenom} {new_user.nom} a créé un nouveau compte.",
                action_status="non_lu"
            )
            db.add(notif)
        db.commit()

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
        province_sujet = db.query(Sujet).filter(Sujet.titre == user.province).first()

        # Si pas encore de sujet  on le crée
        if not province_sujet:
            province_sujet = Sujet(
                titre=user.province,
                idCreateur=user.id  #  Id de l’utilisateur connecté !
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
def get_current_user_me(request: Request, db: Session = Depends(get_db)):
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
        print(user.id)
        return {
            "id":user.id,
            "nom": user.nom,
            "prenom": user.prenom,
            "role": user.role,
            "email": user.email,
            "image": image_url,
            "email": user.email,
            "province": user.province,
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







############O T  P################
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
   


@router.post("/modifPassword")
def modif_password_endpoint(data: ChangePassword, db: Session = Depends(get_db)):
    print(f"Données reçues : email={data.email}, mot_de_passe={data.mot_de_passe}")
    
    try:
        success = modif_password(data.email, data.mot_de_passe, db)
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
    user = verify_user_password(db, data.email, data.mot_de_passe)
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

@router.post("/newPassword")
def update_password_endpoint(data: ChangePassword, db: Session = Depends(get_db)):
    print(data)
    try:
        modif_password(user_id=data.id, mot_de_passe=data.mot_de_passe, db=db)
        return {"success": True, "message": "Mot de passe modifié avec succès !"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))