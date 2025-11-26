from sqlalchemy.orm import Session
from models.models import Formation,Livre
from schemas.user_schemas import FormationCreate, FormationUpdate


def get_all_formations(db: Session):
    return db.query(Formation).order_by(Formation.idFormation.desc()).all()

def create_formation(db: Session, formation: FormationCreate):
    new_form = Formation(
        titre=formation.titre,
        description=formation.description,
        image=formation.image
    )
    db.add(new_form)
    db.commit()
    db.refresh(new_form)
    return new_form

def update_formation(db: Session, id: int, formation: FormationUpdate):
    form = db.query(Formation).filter(Formation.idFormation == id).first()
    if not form:
        return None

    form.titre = formation.titre
    form.description = formation.description
    form.image = formation.image
    db.commit()
    db.refresh(form)
    return form

def delete_formation(db: Session, id: int):
    form = db.query(Formation).filter(Formation.idFormation == id).first()
    if not form:
        return None
    db.query(Livre).filter(Livre.idFormation == id).delete(synchronize_session=False)
    
    db.delete(form)
    db.commit()
    return True


