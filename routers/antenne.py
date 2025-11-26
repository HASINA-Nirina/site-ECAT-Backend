from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from Core.database import get_db
from schemas.user_schemas import AntenneCreate, AntenneUpdate, AntenneOut
from Controllers.antenne_controller import create_antenne,get_all_antennes,get_antenne_by_id,update_antenne,delete_antenne

router = APIRouter(prefix="/antenne", tags=["Antenne"])

@router.post("/NewAntenne", response_model=AntenneOut)
def create_antenne_route(antenne: AntenneCreate, db: Session = Depends(get_db)):
    return create_antenne(db, antenne)

@router.get("/ReadAntenne", response_model=list[AntenneOut])
def list_antennes_route(db: Session = Depends(get_db)):
    return get_all_antennes(db)
        
@router.get("/ReadAntenneById/{antenne_id}", response_model=AntenneOut)
def get_antenne_route(antenne_id: int, db: Session = Depends(get_db)):
    return get_antenne_by_id(db, antenne_id)
 
@router.put("/UpdateAntenne/{antenne_id}", response_model=AntenneOut)
def update_antenne_route(antenne_id: int, antenne_data: AntenneUpdate, db: Session = Depends(get_db)):
    return update_antenne(db, antenne_id, antenne_data)

@router.delete("/DeleteAntenne/{antenne_id}")
def delete_antenne_route(antenne_id: int, db: Session = Depends(get_db)):
    return delete_antenne(db, antenne_id)
