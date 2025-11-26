from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from Controllers.formation_Controllers import (
    get_all_formations, create_formation, update_formation, delete_formation
)
from schemas.user_schemas import FormationResponse,FormationCreate,FormationUpdate
from Core.database import get_db
import shutil, os
from models.models import Formation 


router = APIRouter(
    prefix="/formation",
    tags=["Formation"]
)
UPLOAD_DIR = "uploads/formation"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/ReadFormation", response_model=list[FormationResponse])
def list_formations(db: Session = Depends(get_db)):
    return get_all_formations(db)


@router.post("/NewFormation", response_model=FormationResponse)
async def add_formation(
    titre: str = Form(...),
    description: str = Form(...),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    
    try:
        image_path = None
        if image:
            # Création du répertoire 'uploads' s'il n'existe pas
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            
            # Chemin complet du fichier dans le répertoire 'uploads'
            file_location = os.path.join(UPLOAD_DIR, image.filename)
            
            # Écriture du fichier
            with open(file_location, "wb") as f:
                shutil.copyfileobj(image.file, f)
            
            # Chemin relatif stocké dans la base de données (ex: /uploads/mon_image.jpg)
            image_path = f"/{UPLOAD_DIR}/{image.filename}"
        new_form = Formation(
            titre=titre,
            description=description,
            image=image_path
        )
        db.add(new_form)
        db.commit()
        db.refresh(new_form)

        return FormationResponse(
            idFormation=new_form.id,
            titre=new_form.titre,
            description=new_form.description,
            image=new_form.image
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.put("/UpdateFormation/{id}", response_model=FormationResponse)
async def edit_formation(
    id: int,
    titre: str = Form(...),
    description: str = Form(...),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    # Récupération de la formation existante
    form = db.query(Formation).filter(Formation.idFormation == id).first()
    if not form:
        raise HTTPException(404, "Formation non trouvée")

    try:
        image_path = form.image  # on garde l’ancienne si pas de nouvelle

        if image:
            os.makedirs(UPLOAD_DIR, exist_ok=True)

            file_location = os.path.join(UPLOAD_DIR, image.filename)

            with open(file_location, "wb") as f:
                shutil.copyfileobj(image.file, f)

            image_path = f"/{UPLOAD_DIR}/{image.filename}"

        # Mise à jour
        form.titre = titre
        form.description = description
        form.image = image_path

        db.commit()
        db.refresh(form)

        return FormationResponse(
            idFormation=form.idFormation,
            titre=form.titre,
            description=form.description,
            image=form.image
        )

    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete("/DeleteFormation/{id}")
def remove_formation(id: int, db: Session = Depends(get_db)):
    result = delete_formation(db, id)
    if not result:
        raise HTTPException(404, "Formation non trouvée")
    return {"message": "Formation supprimée avec succès"}


    
