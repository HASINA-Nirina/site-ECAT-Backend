from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from models.models import User, Paiement, Formation, Notification
from schemas.user_schemas import PaymentStatus
from datetime import datetime, timedelta
from typing import Dict, List
from fastapi import HTTPException

def get_dashboard_stats(db: Session, current_user: User) -> Dict:
    """
    Récupère les statistiques du dashboard pour un Admin Local.
    Toutes les données (sauf formations) sont filtrées par la province de l'admin.
    """
    
    # Vérifier que l'utilisateur est un Admin Local
    if current_user.role != "Admin Local":
        raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur local.")
    
    if not current_user.province:
        raise HTTPException(status_code=400, detail="L'administrateur local doit avoir une province assignée.")
    
    province = current_user.province
    
    # 1. Étudiants gérés : Nombre de User avec role "etudiante" dans cette province
    etudiants_count = (
        db.query(User)
        .filter(
            User.role == "etudiante",
            User.province == province
        )
        .count()
    )
    
    # 2. Revenus Locaux : Somme des montants de paiements approuvés (SUCCESSFUL) pour cette province
    revenus_locaux = (
        db.query(func.sum(Paiement.montant))
        .join(User, Paiement.idUtilisateur == User.id)
        .filter(
            User.province == province,
            Paiement.status == PaymentStatus.SUCCESS
        )
        .scalar()
    ) or 0.0
    
    # 3. Formations Actives : Nombre total de formations (global, pas filtré par province)
    formations_count = db.query(Formation).count()
    
    # 4. Graphique Barre : Inscriptions par mois sur les 6 derniers mois
    # Utilisation des notifications de type "nouvelle_inscription" pour avoir les dates
    inscriptions_data = []
    six_mois_avant = datetime.now() - timedelta(days=180)
    
    # Récupérer toutes les notifications d'inscription pour cette province
    # Les notifications sont créées lors de l'inscription d'un étudiant
    notifications_inscription = (
        db.query(Notification)
        .join(User, Notification.related_user_id == User.id)
        .filter(
            User.role == "etudiante",
            User.province == province,
            Notification.type == "nouvelle_inscription",
            Notification.created_at >= six_mois_avant
        )
        .all()
    )
    
    # Grouper par mois
    mois_counts = {}
    for notif in notifications_inscription:
        mois_key = notif.created_at.strftime("%Y-%m")
        mois_counts[mois_key] = mois_counts.get(mois_key, 0) + 1
    
    # Construire les données pour les 6 derniers mois
    for i in range(5, -1, -1):  # 6 derniers mois (5, 4, 3, 2, 1, 0)
        date_reference = datetime.now() - timedelta(days=30 * i)
        mois_key = date_reference.strftime("%Y-%m")
        count = mois_counts.get(mois_key, 0)
        
        # Format court du mois (Jan, Fév, etc.)
        mois_short = date_reference.strftime("%b")
        inscriptions_data.append({
            "name": mois_short,
            "Inscrits": count
        })
    
    # 5. Graphique Circulaire : Répartition des statuts de paiement pour cette province
    paiements_status = (
        db.query(
            Paiement.status,
            func.count(Paiement.idPaiement).label('count')
        )
        .join(User, Paiement.idUtilisateur == User.id)
        .filter(User.province == province)
        .group_by(Paiement.status)
        .all()
    )
    
    # Formatage des données pour le Pie Chart
    pie_data = []
    
    for status_tuple in paiements_status:
        status = status_tuple[0]
        count = status_tuple[1]
        status_label = status.value if hasattr(status, 'value') else str(status)
        # Traduire les labels
        label_map = {
            "PENDING": "En attente",
            "SUCCESS": "Validé",
            "FAILED": "Échoué",
            "CANCELLED": "Annulé"
        }
        label = label_map.get(status_label, status_label)
        pie_data.append({
            "name": label,
            "value": count
        })
    
    return {
        "etudiants_geres": etudiants_count,
        "revenus_locaux": float(revenus_locaux),
        "formations_actives": formations_count,
        "inscriptions_mensuelles": inscriptions_data,
        "repartition_paiements": pie_data
    }

