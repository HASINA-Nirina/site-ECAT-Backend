from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_
from Core.database import get_db
from Controllers.forum_contronllers import ajouter_message, get_all_sujets, get_sujet_by_id, create_sujet
from schemas.user_schemas import MessageCreate,SujetOut,SujetResponse
from models.models import Message,Sujet, User
from typing import List, Optional, Union


router = APIRouter(prefix="/forum", tags=["Forum"])

@router.post("/ajouter")
def add_message(data: MessageCreate, db: Session = Depends(get_db)):
    return ajouter_message(db, data)


@router.get("/sujet", response_model=list[SujetOut])
def list_sujets(db: Session = Depends(get_db)):
    return get_all_sujets(db)

@router.post("/sujets", response_model=SujetResponse)
async def create_new_sujet(
    titre: str = Form(...),
    idCreateur: int = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    return await create_sujet(db, titre, idCreateur, image)

@router.get("/{idSujet}", response_model=SujetOut)
def show_sujet(idSujet: int, db: Session = Depends(get_db)):
    sujet = get_sujet_by_id(db, idSujet)
    if not sujet:
        raise HTTPException(status_code=404, detail="Sujet non trouvé")
    return sujet

@router.get("/ReadSujet/{idUser}", response_model=List[SujetResponse])
def read_sujet_by_user(idUser: int, db: Session = Depends(get_db)):
    # Récupérer l'utilisateur
    user = db.query(User).filter(User.id == idUser).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    sujets = []

    if user.role == "admin":
        # Récupérer tous les sujets créés par cet admin (nouveaux sujets), en excluant "Administratif" et "Forum administratif"
        nouveaux_sujets = db.query(Sujet).filter(
            Sujet.idCreateur == idUser,
            Sujet.titre != "Administratif",
            Sujet.titre != "Forum administratif"
        ).order_by(Sujet.date_creation.desc()).all()
        
        # Récupérer le sujet par défaut : Administratif ou Forum administratif
        admin_sujet = db.query(Sujet).filter(
            or_(Sujet.titre == "Forum administratif", Sujet.titre == "Administratif")
        ).first()
        
        # Combiner : nouveaux sujets en premier, puis Forum administratif
        sujets = list(nouveaux_sujets)
        if admin_sujet:
            sujets.append(admin_sujet)
    
    elif user.role == "admin_local":
        # Récupérer les sujets créés par cet admin local
        nouveaux_sujets = db.query(Sujet).filter(Sujet.idCreateur == idUser).order_by(Sujet.date_creation.desc()).all()
        
        #  sujets par défaut : Forum administratif + Forum local (province)
        admin_sujet = db.query(Sujet).filter(Sujet.titre == "Forum administratif").first()
        local_sujet = db.query(Sujet).filter(
            Sujet.titre.like("%Forum%"), Sujet.province == user.province
        ).first()
        
        # Combiner : nouveaux sujets en premier
        sujets = nouveaux_sujets
        if admin_sujet and admin_sujet not in nouveaux_sujets:
            sujets.append(admin_sujet)
        if local_sujet and local_sujet not in nouveaux_sujets:
            sujets.append(local_sujet)
    
    elif user.role == "etudiant":
        #  sujet par défaut : Forum de sa province
        sujet = db.query(Sujet).filter(
            Sujet.titre.like("%Forum%"), Sujet.province == user.province
        ).first()
        if sujet:
            sujets.append(sujet)
    
    else:
        raise HTTPException(status_code=403, detail="Rôle non autorisé")
    
    return sujets

@router.post("/NewSujet", response_model=SujetResponse)
async def creer_sujet(
    titre: str = Form(...),
    idCreateur: int = Form(...),
    image: Optional[Union[UploadFile, str]] = File(None),
    db: Session = Depends(get_db)
):
    """
    Route pour créer un nouveau sujet.
    Accepte image = UploadFile OU image = "" OU image absent.
    """
    
    # Si image = "" → convertir en None pour éviter l'erreur
    if isinstance(image, str) and image == "":
        image = None

    # Si image est réellement UploadFile et possède un filename
    image_file = None
    if isinstance(image, UploadFile) and image.filename:
        image_file = image

    return await create_sujet(db, titre, idCreateur, image_file)
