from sqlalchemy.orm import Session
from models.models import Message,Sujet
from schemas.user_schemas import MessageCreate
def ajouter_message(db: Session, data: MessageCreate):
    message = Message(
        idSender=data.idSender,
        idSujet=data.idSujet,
        contenu=data.contenu,
        idParentMessage=data.idParentMessage
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_all_sujets(db: Session):
    return db.query(Sujet).all()

def get_sujet_by_id(db: Session, idSujet: int):
    return db.query(Sujet).filter(Sujet.idSujet == idSujet).first()
