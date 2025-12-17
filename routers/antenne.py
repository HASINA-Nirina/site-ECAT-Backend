from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from Core.database import get_db
from schemas.user_schemas import AntenneCreate, AntenneUpdate, AntenneOut
from Controllers.antenne_controller import create_antenne,get_all_antennes,get_antenne_by_id,update_antenne,delete_antenne
from Controllers.historique_controller import create_historique_for_super_admin
from models.models import User
from Core.config import SECRET_KEY, ALGORITHM
import jwt

router = APIRouter(prefix="/antenne", tags=["Antenne"])

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

@router.post("/NewAntenne", response_model=AntenneOut)
def create_antenne_route(antenne: AntenneCreate, request: Request, db: Session = Depends(get_db)):
    new_antenne = create_antenne(db, antenne)
    
    # Enregistrer l'historique
    current_user = get_current_user_from_request(request, db)
    if current_user:
        try:
            create_historique_for_super_admin(
                db=db,
                id_acteur=current_user.id,
                action_type="CREATION_ANTENNE",
                description=f"L'Admin Super {current_user.prenom} {current_user.nom} a créé l'antenne {new_antenne.province}.",
                target_id=new_antenne.id
            )
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de l'historique: {e}")
    
    return new_antenne

@router.get("/ReadAntenne", response_model=list[AntenneOut])
def list_antennes_route(db: Session = Depends(get_db)):
    return get_all_antennes(db)
        
@router.get("/ReadAntenneById/{antenne_id}", response_model=AntenneOut)
def get_antenne_route(antenne_id: int, db: Session = Depends(get_db)):
    return get_antenne_by_id(db, antenne_id)
 
@router.put("/UpdateAntenne/{antenne_id}", response_model=AntenneOut)
def update_antenne_route(antenne_id: int, antenne_data: AntenneUpdate, request: Request, db: Session = Depends(get_db)):
    updated_antenne = update_antenne(db, antenne_id, antenne_data)
    
    # Enregistrer l'historique
    current_user = get_current_user_from_request(request, db)
    if current_user:
        try:
            create_historique_for_super_admin(
                db=db,
                id_acteur=current_user.id,
                action_type="MODIF_ANTENNE",
                description=f"L'Admin Super {current_user.prenom} {current_user.nom} a modifié l'antenne {updated_antenne.province}.",
                target_id=updated_antenne.id
            )
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de l'historique: {e}")
    
    return updated_antenne

@router.delete("/DeleteAntenne/{antenne_id}")
def delete_antenne_route(antenne_id: int, request: Request, db: Session = Depends(get_db)):
    # Récupérer l'antenne avant suppression pour l'historique
    from models.models import Antenne
    antenne_to_delete = db.query(Antenne).filter(Antenne.id == antenne_id).first()
    province_name = antenne_to_delete.province if antenne_to_delete else "Inconnue"
    
    result = delete_antenne(db, antenne_id)
    
    # Enregistrer l'historique
    current_user = get_current_user_from_request(request, db)
    if current_user and antenne_to_delete:
        try:
            create_historique_for_super_admin(
                db=db,
                id_acteur=current_user.id,
                action_type="SUPPR_ANTENNE",
                description=f"L'Admin Super {current_user.prenom} {current_user.nom} a supprimé l'antenne {province_name}.",
                target_id=antenne_id
            )
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de l'historique: {e}")
    
    return result
