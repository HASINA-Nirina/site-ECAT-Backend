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
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # sauvegarder le fichier
    file_location = os.path.join(UPLOAD_DIR, image.filename)
    with open(file_location, "wb") as f:
        shutil.copyfileobj(image.file, f)
    
    # créer l'enregistrement DB
    new_form = Formation(
        titre=titre,
        description=description,
        image=f"/{UPLOAD_DIR}/{image.filename}"  
    )
    db.add(new_form)
    db.commit()
    db.refresh(new_form)
    
    return new_form

@router.put("/UpdateFormation/{id}", response_model=FormationResponse)
def edit_formation(id: int, data: FormationUpdate, db: Session = Depends(get_db)):
    result = update_formation(db, id, data)
    if not result:
        raise HTTPException(404, "Formation non trouvée")
    return result

@router.delete("/DeleteFormation/{id}")
def remove_formation(id: int, db: Session = Depends(get_db)):
    result = delete_formation(db, id)
    if not result:
        raise HTTPException(404, "Formation non trouvée")
    return {"message": "Formation supprimée avec succès"}


    
