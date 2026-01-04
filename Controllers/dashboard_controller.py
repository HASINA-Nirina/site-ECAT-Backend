from sqlalchemy.orm import Session
from sqlalchemy import func
from models.models import User, Antenne
from typing import Dict, List
from fastapi import HTTPException

def get_registrations_by_antenne(db: Session) -> Dict[str, List]:
    """
    Récupère le nombre d'étudiants inscrits par antenne (province).
    Utilise SQLAlchemy pour faire un join entre User et Antenne,
    compte les utilisateurs par province, et filtre par rôle 'etudiante'.
    
    Returns:
        Dict avec 'labels' (list de provinces) et 'data' (list de counts)
    """
    try:
        # Requête avec join entre User et Antenne
        # Utilisation de func.count et group_by pour l'agrégation en base de données
        results = (
            db.query(
                Antenne.province,
                func.count(User.id).label('count')
            )
            .join(User, User.province == Antenne.province)
            .filter(User.role == 'etudiante')
            .group_by(Antenne.province)
            .all()
        )
        
        
        # Extraire les labels (provinces) et les données (counts)
        labels = []
        data = []
        
        for province, count in results:
            labels.append(province)
            data.append(count)
        
        return {
            "labels": labels,
            "data": data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")

