from fastapi import APIRouter, Depends, HTTPException,UploadFile, File, Form
from sqlalchemy.orm import Session
from Core.database import get_db
from models.models import Livre
from Controllers.livre_controllers import (
    update_livre_controller, delete_livre_controller,
    get_all_livres, create_livre,get_livres,get_livres_by_formation,
     debloque_livre, get_livre_debloque_by_idetudiant,check_user_livre_access
)
from schemas.user_schemas import LivreCreate, LivreUpdate, LivreResponse, LivreDebloque,LivreDebloqueResponse, UserLivreAccessCheck
import os
router = APIRouter(prefix="/livre", tags=["Livre"])

@router.get("/ReadLivres/", response_model=list[LivreResponse])
def read_livres(db: Session = Depends(get_db)):
    return get_all_livres(db)

@router.get("/ReadLivres/{idFormation}/{idUser}")
def read_livres_by_formation(idFormation: int, idUser: int, db: Session = Depends(get_db)):
    return get_livres_by_formation(db, idFormation, idUser)


@router.get("/ReadLivresLocal/{idFormation}")
def read_livres_by_formation(idFormation: int, db: Session = Depends(get_db)):
    return get_livres(db, idFormation)
  
@router.post("/NewLivre/")
async def new_livre(
    idFormation: int = Form(...),
    titre: str = Form(...),
    auteur: str = Form(...),
    description: str = Form(""),
    prix: str = Form("0"),
    urlPdf: UploadFile = File(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    fichier_path = None
    if urlPdf is not None:  
        ext = os.path.splitext(urlPdf.filename)[1]
        original_name = os.path.splitext(urlPdf.filename)[0]
        ext = os.path.splitext(urlPdf.filename)[1]
        save_name = f"{original_name}{ext}"
        fichier_path = os.path.join(upload_dir, save_name)
        with open(fichier_path, "wb") as f:
            f.write(await urlPdf.read())

    image_path = f"uploads/{image.filename}" if image else ""
    if image:
        with open(image_path, "wb") as f:
            f.write(image.file.read())

    
    livre = LivreCreate(
        idFormation=idFormation,
        titre=titre,
        auteur=auteur,
        description=description,
        prix=prix,
        urlPdf=save_name,
        
    )

    db_livre = create_livre(db, livre, save_name, image_path)
    return db_livre

@router.put("/UpdateLivre/{livre_id}")
async def update_livre(
    livre_id: int,
    titre: str = Form(...),
    auteur: str = Form(...),
    prix: str = Form(...),
    description: str = Form(...),
    urlPdf: UploadFile = None,
    image: UploadFile = None,
    db: Session = Depends(get_db)
):
    data = {
        "titre": titre,
        "auteur": auteur,
        "prix": prix,
        "description": description
    }

    return update_livre_controller(db, livre_id, data, urlPdf, image)


@router.delete("/DeleteLivre/{livre_id}")
async def delete_livre(livre_id: int, db: Session = Depends(get_db)):
    return delete_livre_controller(db, livre_id)



@router.post("/Debloque")
def new_access(data:LivreDebloque ,db: Session = Depends(get_db)):
    access= debloque_livre(db, data)
    return access

@router.post("/livreDebloqueEtudiant/{iduser}")
def lire_livres_debloque(iduser: int, db: Session = Depends(get_db)):
    return get_livre_debloque_by_idetudiant(db , iduser)  

