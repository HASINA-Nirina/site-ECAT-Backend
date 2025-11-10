from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from models.models import Livre,UserLivreAccess
from schemas.user_schemas import LivreCreate, LivreUpdate, LivreDebloque
from sqlalchemy.orm import Session
import shutil
import os


UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def get_all_livres(db: Session):
    Livre = db.query(Livre).all()
    


def get_livres_by_formation(db: Session, idFormation: int, idUser: int):
    # Sélectionner tous les livres appartenant à une formation
    livres = db.query(Livre).filter(Livre.idFormation == idFormation).all()
    result = []

    for livre in livres:
        has_access = check_user_livre_access(db, idUser, livre.idLivre)
        access = True if has_access else False
        print(livre.image)

        result.append({
            "id": livre.idLivre,
            "title": livre.titre,
            "author": livre.auteur,
            "image": livre.image,
            "pdf": livre.urlPdf,
            "prix": livre.prix,
            "access": access
        })

    return result

def get_livres(db: Session, idFormation: int):
    # Sélectionner tous les livres appartenant à une formation
    livres = db.query(Livre).filter(Livre.idFormation == idFormation).all()
    result = []

    for livre in livres:
        print(livre.image)

        result.append({
            "id": livre.idLivre,
            "title": livre.titre,
            "author": livre.auteur,
            "image": livre.image,
            "pdf": livre.urlPdf,
            "prix": livre.prix,
            "description": livre.description,
        })

    return result

def get_livre_debloque_by_idetudiant(db: Session, iduser: int):
    
    livres = (
        db.query(Livre)
        .join(UserLivreAccess, Livre.idLivre == UserLivreAccess.idLivre)
        .filter(UserLivreAccess.idUser == iduser)
        .all()
    )
    print(len(livres))
    return [
        {
            "id": livre.idLivre,
            "title": livre.titre,
            "author": livre.auteur,
            "image": livre.urlPdf,
            "user":iduser
        }
        for livre in livres
        
    ]



def create_livre(db: Session, livre: LivreCreate, pdf_path: str , image_path: str ):
    db_livre = Livre(
        idFormation=livre.idFormation,
        titre=livre.titre,
        auteur=livre.auteur,
        urlPdf=pdf_path,
        image=image_path,
        description=livre.description,
        prix=livre.prix
    )
    db.add(db_livre)
    db.commit()
    db.refresh(db_livre)
    return db_livre




def update_livre_controller(db: Session, livre_id: int, data: dict, file_pdf: UploadFile = None, file_image: UploadFile = None):
    livre = db.query(Livre).filter(Livre.idLivre == livre_id).first()
    if not livre:
        raise HTTPException(status_code=404, detail="Livre non trouvé")

    # Mise à jour des champs texte
    for key, value in data.items():
        setattr(livre, key, value)

    # Upload PDF
    if file_pdf:
        pdf_path = f"{UPLOAD_DIR}/pdf_{livre_id}.pdf"
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file_pdf.file, buffer)
        livre.urlPdf = pdf_path

    # Upload Image
    if file_image:
        image_path = f"{UPLOAD_DIR}/image_{livre_id}.jpg"
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file_image.file, buffer)
        livre.image = image_path

    db.commit()
    db.refresh(livre)
    return livre


def delete_livre_controller(db: Session, livre_id: int):
    livre = db.query(Livre).filter(Livre.idLivre == livre_id).first()
    if not livre:
        raise HTTPException(status_code=404, detail="Livre non trouvé")

    # Supprimer fichiers liés
    if livre.urlPdf and os.path.exists(livre.urlPdf):
        os.remove(livre.urlPdf)

    if livre.image and os.path.exists(livre.image):
        os.remove(livre.image)

    db.delete(livre)
    db.commit()

    return {"message": "Livre supprimé avec succès"}

def debloque_livre(db: Session, data: LivreDebloque):
    db_access = UserLivreAccess(
        idUser=data.idUser,
        idLivre=data.idLivre,
        canAccess=True
    )
    db.add(db_access)
    db.commit()
    db.refresh(db_access)
    return db_access

def check_user_livre_access(db: Session, iduser: int, idlivre: int) -> bool:
    access = db.query(UserLivreAccess)\
        .filter(UserLivreAccess.idUser == iduser)\
        .filter(UserLivreAccess.idLivre == idlivre)\
        .first()
    if access and access.canAccess:
        return True
    return False