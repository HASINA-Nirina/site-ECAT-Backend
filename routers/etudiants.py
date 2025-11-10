from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session

from Core.database import get_db
from Controllers.user_controllers import get_etudiants, get_etudiants_by_province, get_all_etudiant, get_current_user
from schemas.user_schemas import EtudiantOut, EtudiantResponse

router = APIRouter(prefix="/etudiants", tags=["etudiants"])


@router.get("/by-province", response_model=List[EtudiantOut])
def read_etudiants_current_user(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Retourne les étudiants de la même province/antenne que l'utilisateur courant (Admin local)."""
    return get_etudiants_by_province(current_user=current_user, db=db)


@router.get("/by-province/{province}", response_model=List[EtudiantOut])
def read_etudiants_by_province(province: str, db: Session = Depends(get_db)):
    """Retourne les étudiants pour une province/antenne donnée."""
    return get_etudiants(province=province, db=db)


@router.get("/all", response_model=List[EtudiantResponse])
def read_all_etudiants(db: Session = Depends(get_db)):
    """Retourne tous les étudiants (utilisé par les super admins)."""
    return get_all_etudiant(db)
