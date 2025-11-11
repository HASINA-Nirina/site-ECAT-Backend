from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.models import Paiement, User

# Récupérer tous les paiements
def get_all_paiements(db: Session):
    paiements = db.query(Paiement).all()
    return paiements

# Récupérer un paiement par ID
def get_paiement_by_id(db: Session, idPaiement: int):
    paiement = db.query(Paiement).filter(Paiement.idPaiement == idPaiement).first()
    if not paiement:
        raise HTTPException(status_code=404, detail="Paiement introuvable")
    return paiement
def get_paiements_par_province(db: Session, current_user: User):
    if current_user.role != "Admin Local":
        raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur local.")

    paiements = (
        db.query(Paiement)
        .join(User, Paiement.idUtilisateur == User.id)
        .filter(User.province == current_user.province)
        .all()
    )

    if not paiements:
        return {"message": "Aucun paiement trouvé pour cette province"}

    result = []
    for p in paiements:
        result.append({
            "id": p.idPaiement,
            "nom": f"{p.utilisateur.nom} {p.utilisateur.prenom}",
            "montant": p.montant,
            "methode": p.operateur,
            "date": p.date_creation.strftime("%Y-%m-%d"),
        })

    return {
        "province": current_user.province,
        "total": len(result),
        "paiements": result
    }