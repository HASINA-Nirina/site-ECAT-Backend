from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, extract
from models.models import User, Formation, Livre, UserLivreAccess, Paiement
from schemas.user_schemas import PaymentStatus
from datetime import datetime, timedelta
from typing import Dict
from fastapi import HTTPException

def get_student_dashboard_stats(db: Session, current_user: User) -> Dict:
    """
    Récupère les statistiques du dashboard pour un Étudiant.
    Toutes les données sont filtrées par l'ID de l'étudiant (current_user.id).
    """
    
    # Vérifier que l'utilisateur est un étudiant
    if current_user.role != "etudiante":
        raise HTTPException(status_code=403, detail="Accès réservé aux étudiants.")
    
    user_id = current_user.id
    
    # 1. Formations : Nombre distinct de Formations pour lesquelles l'étudiant a débloqué au moins un livre
    formations_count = (
        db.query(distinct(Formation.idFormation))
        .join(Livre, Formation.idFormation == Livre.idFormation)
        .join(UserLivreAccess, Livre.idLivre == UserLivreAccess.idLivre)
        .filter(
            UserLivreAccess.idUser == user_id,
            UserLivreAccess.canAccess == True
        )
        .count()
    )
    
    # 2. Paiements : Nombre total de Paiements avec status SUCCESS
    paiements_count = (
        db.query(Paiement)
        .filter(
            Paiement.idUtilisateur == user_id,
            Paiement.status == PaymentStatus.SUCCESS
        )
        .count()
    )
    
    # 3. Livres : Nombre total de Livres avec accès valide (canAccess=True)
    livres_count = (
        db.query(Livre)
        .join(UserLivreAccess, Livre.idLivre == UserLivreAccess.idLivre)
        .filter(
            UserLivreAccess.idUser == user_id,
            UserLivreAccess.canAccess == True
        )
        .count()
    )
    
    # 4. Historique : Nombre de livres débloqués par mois sur les 6 derniers mois
    six_mois_avant = datetime.now() - timedelta(days=180)
    
    # Récupérer tous les accès aux livres de l'étudiant créés dans les 6 derniers mois
    # Note: UserLivreAccess n'a pas de date_creation visible dans le modèle
    # On va utiliser la date_creation du paiement associé comme proxy, ou créer une logique alternative
    
    # Si UserLivreAccess n'a pas de date, on peut utiliser la date du paiement associé
    # Sinon, on peut utiliser une approximation basée sur l'ID ou une autre logique
    
    # Pour l'instant, utilisons une approche basée sur les paiements validés qui débloquent des livres
    # Les livres sont débloqués quand un paiement est validé, donc on peut utiliser la date du paiement
    
    # Récupérer les paiements validés avec leurs dates
    paiements_valides = (
        db.query(
            extract('year', Paiement.date_creation).label('year'),
            extract('month', Paiement.date_creation).label('month'),
            func.count(distinct(Paiement.idLivre)).label('count')
        )
        .filter(
            Paiement.idUtilisateur == user_id,
            Paiement.status == PaymentStatus.SUCCESS,
            Paiement.date_creation >= six_mois_avant
        )
        .group_by(
            extract('year', Paiement.date_creation),
            extract('month', Paiement.date_creation)
        )
        .all()
    )
    
    # Construire un dictionnaire mois -> nombre de livres
    mois_counts = {}
    for year, month, count in paiements_valides:
        mois_key = f"{year}-{month:02d}"
        mois_counts[mois_key] = count
    
    # Construire l'historique pour les 6 derniers mois
    historique = []
    for i in range(5, -1, -1):  # 6 derniers mois (5, 4, 3, 2, 1, 0)
        date_reference = datetime.now() - timedelta(days=30 * i)
        mois_key = date_reference.strftime("%Y-%m")
        
        # Nombre de livres débloqués ce mois (via paiements)
        livres_ce_mois = mois_counts.get(mois_key, 0)
        
        # Format court du mois
        mois_short = date_reference.strftime("%b")
        
        historique.append({
            "mois": mois_short,
            "livres": livres_ce_mois
        })
    
    return {
        "formations": formations_count,
        "paiements": paiements_count,
        "livres": livres_count,
        "historique": historique
    }

