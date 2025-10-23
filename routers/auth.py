from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Core.database import get_db
from schemas.user_schemas import UserCreate, UserLogin ,EmailRequest, VerifyOTPRequest, ChangePassword
from Controllers.user_controllers import create_user, authenticate_user_role, new_Password
from models.models import User
#from schemas.Otp_shemas import SendOTPRequest
from Controllers.Otp_controlllers import sendOtp,verify_otp 


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/Etudiantregister")
def register(data: UserCreate, db: Session = Depends(get_db)):
    # Vérifier si l'email existe déjà
    
    print("Verification de ")
    existing_user = db.query(User).filter(User.email == data.email).first()

    if existing_user:
        
        print("email deja utilise")
        return {"error":"Cet e-mail est déjà utilisé."}

    # Si tout va bien, créer l'utilisateur
    
    db_user = create_user(db, data)
    return {"message": "Utilisateur créé avec succès", "user": db_user.email}

@router.post("/test")
def test():
    print(" test succes")

@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    print(" Données reçues :", credentials)
    result = authenticate_user_role(credentials.email, credentials.mot_de_passe, db)
    print("Résultat de l'authentification :", result)
    
    if isinstance(result, dict) and "error" in result:
        return result
    return result

@router.post("/sendOtp")
def send_otp(data:EmailRequest , db: Session = Depends(get_db)):
    print(" Données reçues :", data)
    existing_user = db.query(User).filter(User.email == data.email).first()

    if existing_user:
        sendOtp(data.email, db)
        return {"message": "otp envoyer"}

    print("email n existe pas ")
    return {"error":"Cet e-mail email n existe pas"}

@router.post("/verify")
def check_otp(data: VerifyOTPRequest, db: Session = Depends(get_db)):
    return  verify_otp(data.email, data.code, db)
   
@router.post("/modifPassword")
def new_password(data: ChangePassword,db: Session = Depends(get_db)):
    print(" Données reçues :", data)
    return new_Password(data.email, data.mot_de_passe, db)


