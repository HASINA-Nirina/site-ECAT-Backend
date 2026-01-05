from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from models.models import Livre, UserLivreAccess, Paiement, User
from schemas.user_schemas import LivreCreate, LivreUpdate, LivreDebloque, PaymentStatus
from sqlalchemy.orm import Session
import shutil
import os


UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def get_all_livres(db: Session, user_province: str = None):
    """
    Récupère tous les livres, filtrés par province si user_province est fourni.
    """
    query = db.query(Livre)
    if user_province:
        query = query.filter(Livre.province == user_province)
    return query.all()
    


def get_livres_by_formation(db: Session, idFormation: int, idUser: int, user_province: str = None):
    """
    Sélectionne tous les livres appartenant à une formation, filtrés par province.
    """
    query = db.query(Livre).filter(Livre.idFormation == idFormation)
    if user_province:
        query = query.filter(Livre.province == user_province)
    livres = query.all()
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

def get_livres(db: Session, idFormation: int, user_province: str = None):
    """
    Sélectionne tous les livres appartenant à une formation, filtrés par province.
    """
    query = db.query(Livre).filter(Livre.idFormation == idFormation)
    if user_province:
        query = query.filter(Livre.province == user_province)
    livres = query.all()
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
    """
    Récupère les livres débloqués par un étudiant, filtrés par sa province.
    """
    # Récupérer la province de l'utilisateur
    user = db.query(User).filter(User.id == iduser).first()
    user_province = user.province if user else None
    
    query = (
        db.query(Livre)
        .join(UserLivreAccess, Livre.idLivre == UserLivreAccess.idLivre)
        .filter(UserLivreAccess.idUser == iduser)
    )
    
    # Filtrer par province si l'utilisateur a une province
    if user_province:
        query = query.filter(Livre.province == user_province)
    
    livres = query.all()
    print(len(livres))
    return [
        {
            "id": livre.idLivre,
            "title": livre.titre,
            "author": livre.auteur,
            "image": livre.image,
            "user":iduser,
            "pdf":livre.urlPdf
        }
        for livre in livres
        
    ]



def create_livre(db: Session, livre: LivreCreate, pdf_path: str, image_path: str, user_province: str = None):
    """
    Crée un nouveau livre avec la province de l'utilisateur connecté.
    """
    db_livre = Livre(
        idFormation=livre.idFormation,
        titre=livre.titre,
        auteur=livre.auteur,
        urlPdf=pdf_path,
        image=image_path,
        description=livre.description,
        prix=livre.prix,
        province=user_province
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
    # 1. Création de l'accès au livre
    db_access = UserLivreAccess(
        idUser=data.idUser,
        idLivre=data.idLivre,
        canAccess=True
    )
    db.add(db_access)

    # 2. Création de l'enregistrement de paiement
    db_paiement = Paiement(
        idUtilisateur=data.idUser,
        idLivre=data.idLivre,
        contact=data.contact,
        montant=data.montant,
        operateur=data.operateur,
        reference=data.reference, 
        status=PaymentStatus.SUCCESS.value
        #  PENDING = "PENDING"
   # SUCCESS = "SUCCESS"
  #  FAILED = "FAILED"

    )
    db.add(db_paiement)

    # 3. Validation finale
    try:
        db.commit()
        db.refresh(db_access)
        return db_access
    except Exception as e:
        db.rollback() # Annule tout en cas d'erreur (ex: référence déjà existante)
        raise e

def check_user_livre_access(db: Session, iduser: int, idlivre: int) -> bool:
    access = db.query(UserLivreAccess)\
        .filter(UserLivreAccess.idUser == iduser)\
        .filter(UserLivreAccess.idLivre == idlivre)\
        .first()
    if access and access.canAccess:
        return True
    return False