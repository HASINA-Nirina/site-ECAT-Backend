from sqlalchemy.orm import Session
from models.models import Antenne
from schemas.user_schemas import AntenneCreate, AntenneUpdate
from fastapi import HTTPException

def create_antenne(db: Session, antenne: AntenneCreate):
    existing = db.query(Antenne).filter(Antenne.province == antenne.province).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cette antenne existe déjà")
    
    new_antenne = Antenne(province=antenne.province)
    db.add(new_antenne)
    db.commit()
    db.refresh(new_antenne)
    return new_antenne

def get_all_antennes(db: Session):
    return db.query(Antenne).all()

def get_antenne_by_id(db: Session, antenne_id: int):
    antenne = db.query(Antenne).filter(Antenne.id == antenne_id).first()
    if not antenne:
        raise HTTPException(status_code=404, detail="Antenne non trouvée")
    return antenne

def update_antenne(db: Session, antenne_id: int, antenne_data: AntenneUpdate):
    antenne = db.query(Antenne).filter(Antenne.id == antenne_id).first()
    if not antenne:
        raise HTTPException(status_code=404, detail="Antenne non trouvée")
    
    antenne.province = antenne_data.province
    db.commit()
    db.refresh(antenne)
    return antenne

def delete_antenne(db: Session, antenne_id: int):
    antenne = db.query(Antenne).filter(Antenne.id == antenne_id).first()
    if not antenne:
        raise HTTPException(status_code=404, detail="Antenne non trouvée")
    
    db.delete(antenne)
    db.commit()
    return {"message": "Antenne supprimée avec succès"}
