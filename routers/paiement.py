from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from Core.database import get_db  
from schemas.user_schemas import PaiementResponse  
from Controllers.paiement_controller import get_all_paiements, get_paiement_by_id,get_paiements_par_province
from Controllers.user_controllers import get_current_user
from models.models import User

router = APIRouter(prefix="/paiement", tags=["Paiement"])

@router.get("/ReadPaiement/")
def read_paiements(db: Session = Depends(get_db)):
    # Retourne une liste déjà transformée par le contrôleur (dicts)
    return get_all_paiements(db)

@router.get("/ReadPaiement/{idPaiement}")
def read_paiement(idPaiement: int, db: Session = Depends(get_db)):
    return get_paiement_by_id(db, idPaiement)

@router.get("/par_province")
def list_paiements_par_province(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_paiements_par_province(db, current_user)

