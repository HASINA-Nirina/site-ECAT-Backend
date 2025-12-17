from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from Controllers.formation_Controllers import (
    get_all_formations, create_formation, update_formation, delete_formation
)
from schemas.user_schemas import FormationResponse,FormationCreate,FormationUpdate
from Core.database import get_db
import shutil, os
from models.models import Formation, User
from Controllers.historique_controller import create_historique_for_super_admin
from Core.config import SECRET_KEY, ALGORITHM
import jwt 


router = APIRouter(
    prefix="/formation",
    tags=["Formation"]
)
UPLOAD_DIR = "uploads/formation"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_current_user_from_request(request: Request, db: Session):
    """Récupère l'utilisateur actuel depuis le token dans la requête."""
    token = request.cookies.get("token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if user_email:
            return db.query(User).filter(User.email == user_email).first()
    except:
        pass
    return None


@router.get("/ReadFormation", response_model=list[FormationResponse])
def list_formations(db: Session = Depends(get_db)):
    return get_all_formations(db)


@router.post("/NewFormation", response_model=FormationResponse)
async def add_formation(
    request: Request,
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

        result = FormationResponse(
            idFormation=new_form.idFormation,
            titre=new_form.titre,
            description=new_form.description,
            image=new_form.image
        )
        
        # Enregistrer l'historique
        current_user = get_current_user_from_request(request, db)
        if current_user:
            try:
                create_historique_for_super_admin(
                    db=db,
                    id_acteur=current_user.id,
                    action_type="CREATION_FORMATION",
                    description=f"L'Admin Super {current_user.prenom} {current_user.nom} a créé la formation '{new_form.titre}'.",
                    target_id=new_form.idFormation
                )
            except Exception as e:
                print(f"Erreur lors de l'enregistrement de l'historique: {e}")
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/UpdateFormation/{id}", response_model=FormationResponse)
async def edit_formation(
    request: Request,
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

        result = FormationResponse(
            idFormation=form.idFormation,
            titre=form.titre,
            description=form.description,
            image=form.image
        )
        
        # Enregistrer l'historique
        current_user = get_current_user_from_request(request, db)
        if current_user:
            try:
                create_historique_for_super_admin(
                    db=db,
                    id_acteur=current_user.id,
                    action_type="MODIF_FORMATION",
                    description=f"L'Admin Super {current_user.prenom} {current_user.nom} a modifié la formation '{form.titre}'.",
                    target_id=form.idFormation
                )
            except Exception as e:
                print(f"Erreur lors de l'enregistrement de l'historique: {e}")
        
        return result

    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete("/DeleteFormation/{id}")
def remove_formation(request: Request, id: int, db: Session = Depends(get_db)):
    # Récupérer la formation avant suppression pour l'historique
    form_to_delete = db.query(Formation).filter(Formation.idFormation == id).first()
    formation_title = form_to_delete.titre if form_to_delete else "Inconnue"
    
    result = delete_formation(db, id)
    if not result:
        raise HTTPException(404, "Formation non trouvée")
    
    # Enregistrer l'historique
    current_user = get_current_user_from_request(request, db)
    if current_user and form_to_delete:
        try:
            create_historique_for_super_admin(
                db=db,
                id_acteur=current_user.id,
                action_type="SUPPR_FORMATION",
                description=f"L'Admin Super {current_user.prenom} {current_user.nom} a supprimé la formation '{formation_title}'.",
                target_id=id
            )
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de l'historique: {e}")
    
    return {"message": "Formation supprimée avec succès"}


    
