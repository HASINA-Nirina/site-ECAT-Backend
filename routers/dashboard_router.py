from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from Core.database import get_db
from Controllers.dashboard_controller import get_registrations_by_antenne
from schemas.dashboard_schemas import InscriptionsByAntenneResponse
from models.models import User


router = APIRouter(prefix="/stats", tags=["Dashboard"])

@router.get("/inscriptions-antenne", response_model=InscriptionsByAntenneResponse)
def inscriptions_by_antenne(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint pour récupérer le nombre d'étudiants inscrits par antenne.
    Retourne les données formatées pour un graphique (labels et data).
    """
    try:
        result = get_registrations_by_antenne(db)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/countetudiantes")
def count_etudiantes(db: Session = Depends(get_db)):
    """
    Compte le nombre total d'utilisateurs ayant le rôle 'etudiante'.
    """

    total = (
        db.query(func.count(User.id))
        .filter(User.role == "etudiante")
        .scalar()
    )

    return {
        "role": "etudiante",
        "total": total
    }