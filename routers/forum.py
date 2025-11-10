from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from Core.database import get_db
from Controllers.forum_contronllers import ajouter_message, get_all_sujets, get_sujet_by_id
from schemas.user_schemas import MessageCreate,SujetOut

router = APIRouter(prefix="/forum", tags=["Forum"])

@router.post("/ajouter")
def add_message(data: MessageCreate, db: Session = Depends(get_db)):
    return ajouter_message(db, data)


@router.get("/sujet", response_model=list[SujetOut])
def list_sujets(db: Session = Depends(get_db)):
    return get_all_sujets(db)

@router.get("/{idSujet}", response_model=SujetOut)
def show_sujet(idSujet: int, db: Session = Depends(get_db)):
    sujet = get_sujet_by_id(db, idSujet)
    if not sujet:
        raise HTTPException(status_code=404, detail="Sujet non trouvé")
    return sujet
