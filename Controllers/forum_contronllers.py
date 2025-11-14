from sqlalchemy.orm import Session
from models.models import Message,Sujet
from schemas.user_schemas import MessageCreate
from fastapi import UploadFile
from typing import Optional
import shutil
import os
import uuid

def ajouter_message(db: Session, data: MessageCreate):
    message = Message(
        idSender=data.idSender,
        idSujet=data.idSujet,
        contenu=data.contenu,
        idParentMessage=data.idParentMessage
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_all_sujets(db: Session):
    return db.query(Sujet).all()

def get_sujet_by_id(db: Session, idSujet: int):
    return db.query(Sujet).filter(Sujet.idSujet == idSujet).first()

async def create_sujet(db: Session, titre: str, idCreateur: int, image: Optional[UploadFile] = None):
    image_path = None
    if image:
        # Générer un nom de fichier unique
        file_extension = os.path.splitext(image.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        upload_dir = "upload/forum"
        os.makedirs(upload_dir, exist_ok=True)
        file_location = os.path.join(upload_dir, unique_filename)
        
        with open(file_location, "wb") as f:
            shutil.copyfileobj(image.file, f)
        
        image_path = f"{unique_filename}"
    
    new_sujet = Sujet(
        titre=titre,
        idCreateur=idCreateur,
        image=image_path
    )
    db.add(new_sujet)
    db.commit()
    db.refresh(new_sujet)
    return new_sujet
