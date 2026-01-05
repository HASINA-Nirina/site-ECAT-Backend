from fastapi import APIRouter, Depends, HTTPException,UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from Core.database import get_db
from models.models import Livre, User
from Controllers.livre_controllers import (
    update_livre_controller, delete_livre_controller,
    get_all_livres, create_livre,get_livres,get_livres_by_formation,
     debloque_livre, get_livre_debloque_by_idetudiant,check_user_livre_access
)
from schemas.user_schemas import LivreCreate, LivreUpdate, LivreResponse, LivreDebloque,LivreDebloqueResponse, UserLivreAccessCheck
from Controllers.historique_controller import create_historique_for_admin_local_super
from Core.config import SECRET_KEY, ALGORITHM
import jwt
import os
router = APIRouter(prefix="/livre", tags=["Livre"])

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

@router.get("/ReadLivres/", response_model=list[LivreResponse])
def read_livres(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_request(request, db)
    user_province = current_user.province if current_user else None
    return get_all_livres(db, user_province)

@router.get("/ReadLivres/{idFormation}/{idUser}")
def read_livres_by_formation(idFormation: int, idUser: int, request: Request, db: Session = Depends(get_db)):
    # Récupérer la province de l'utilisateur connecté (pas celui passé en paramètre)
    current_user = get_current_user_from_request(request, db)
    user_province = current_user.province if current_user else None
    return get_livres_by_formation(db, idFormation, idUser, user_province)


@router.get("/ReadLivresLocal/{idFormation}")
def read_livres_local(idFormation: int, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_request(request, db)
    user_province = current_user.province if current_user else None
    return get_livres(db, idFormation, user_province)
  
@router.post("/NewLivre/")
async def new_livre(
    request: Request,
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
    save_name = ""
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

    # Récupérer l'utilisateur connecté pour sa province
    current_user = get_current_user_from_request(request, db)
    user_province = current_user.province if current_user else None
    
    db_livre = create_livre(db, livre, save_name, image_path, user_province)
    
    # Enregistrer l'historique
    print(current_user)
    if current_user:
        try:
            create_historique_for_admin_local_super(
                db=db,
                id_acteur=current_user.id,
                action_type="CREATION_LIVRE",
                description=f"L'Admin {current_user.prenom} {current_user.nom} a créé le livre '{db_livre.titre}'.",
                target_id=db_livre.idLivre
            )
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de l'historique: {e}")
    
    return db_livre

@router.put("/UpdateLivre/{livre_id}")
async def update_livre(
    request: Request,
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

    updated_livre = update_livre_controller(db, livre_id, data, urlPdf, image)
    
    # Enregistrer l'historique
    current_user = get_current_user_from_request(request, db)
    if current_user:
        try:
            create_historique_for_admin_local_super(
                db=db,
                id_acteur=current_user.id,
                action_type="MODIF_LIVRE",
                description=f"L'Admin {current_user.prenom} {current_user.nom} a modifié le livre '{updated_livre.titre}'.",
                target_id=updated_livre.idLivre
            )
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de l'historique: {e}")
    
    return updated_livre


@router.delete("/DeleteLivre/{livre_id}")
async def delete_livre(request: Request, livre_id: int, db: Session = Depends(get_db)):
    # Récupérer le livre avant suppression pour l'historique
    livre_to_delete = db.query(Livre).filter(Livre.idLivre == livre_id).first()
    livre_title = livre_to_delete.titre if livre_to_delete else "Inconnu"
    
    result = delete_livre_controller(db, livre_id)
    
    # Enregistrer l'historique
    current_user = get_current_user_from_request(request, db)
    if current_user and livre_to_delete:
        try:
            create_historique_for_admin_local_super(
                db=db,
                id_acteur=current_user.id,
                action_type="SUPPR_LIVRE",
                description=f"L'Admin {current_user.prenom} {current_user.nom} a supprimé le livre '{livre_title}'.",
                target_id=livre_id
            )
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de l'historique: {e}")
    
    return result



@router.post("/Debloque")
def new_access(data:LivreDebloque ,db: Session = Depends(get_db)):
    access= debloque_livre(db, data)
    return access

@router.post("/livreDebloqueEtudiant/{iduser}")
def lire_livres_debloque(iduser: int, db: Session = Depends(get_db)):
    return get_livre_debloque_by_idetudiant(db , iduser)  

