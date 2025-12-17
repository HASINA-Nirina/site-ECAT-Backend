from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.models import Historique, User
from typing import List, Tuple
from fastapi import HTTPException

def get_historiques_by_role(
    db: Session,
    current_user: User,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[dict], int]:
    """
    Récupère les historiques filtrés par le rôle de l'utilisateur connecté.
    
    Retourne:
        - Liste des historiques avec les infos de l'acteur
        - Nombre total d'historiques (pour la pagination)
    """
    
    # Définir les visibilités autorisées selon le rôle
    if current_user.role == "admin":
        # Super Admin voit: SUPER_ADMIN, ADMIN_LOCAL_SUPER, GLOBAL
        allowed_visibilities = ["SUPER_ADMIN", "ADMIN_LOCAL_SUPER", "GLOBAL"]
    elif current_user.role == "Admin Local":
        # Admin Local voit: ADMIN_LOCAL_SUPER, GLOBAL
        allowed_visibilities = ["ADMIN_LOCAL_SUPER", "GLOBAL"]
    else:
        # Les autres rôles voient seulement GLOBAL et USER
        allowed_visibilities = ["GLOBAL", "USER"]
    
    # Requête de base avec filtrage par visibilité
    query = (
        db.query(Historique)
        .join(User, Historique.id_acteur == User.id)
        .filter(Historique.role_visibility.in_(allowed_visibilities))
        .order_by(Historique.date_creation.desc())
    )
    
    # Compter le total
    total = query.count()
    
    # Pagination
    offset = (page - 1) * page_size
    historiques = query.offset(offset).limit(page_size).all()
    
    # Formater les résultats avec les infos de l'acteur
    results = []
    for hist in historiques:
        acteur = hist.acteur if hist.acteur else None
        results.append({
            "id": hist.id,
            "id_acteur": hist.id_acteur,
            "action_type": hist.action_type,
            "description": hist.description,
            "target_id": hist.target_id,
            "role_visibility": hist.role_visibility,
            "date_creation": hist.date_creation.isoformat() if hist.date_creation else None,
            "acteur_nom": acteur.nom if acteur else None,
            "acteur_prenom": acteur.prenom if acteur else None,
        })
    
    return results, total

"""
Helper functions pour créer des entrées d'historique.
Ces fonctions peuvent être appelées dans les différents contrôleurs pour enregistrer automatiquement les actions.
"""
from sqlalchemy.orm import Session
from models.models import Historique, User
from datetime import datetime, timezone

def create_historique(
    db: Session,
    id_acteur: int,
    action_type: str,
    description: str,
    target_id: int | None = None,
    role_visibility: str = "GLOBAL"
) -> Historique:
    """
    Crée une entrée d'historique.
    
    Args:
        db: Session de base de données
        id_acteur: ID de l'utilisateur qui a effectué l'action
        action_type: Type d'action (ex: 'CREATION_ANTENNE', 'MODIF_LIVRE')
        description: Description détaillée de l'action
        target_id: ID de l'entité affectée (optionnel)
        role_visibility: Visibilité de l'historique ('SUPER_ADMIN', 'ADMIN_LOCAL_SUPER', 'GLOBAL', 'USER')
    
    Returns:
        L'objet Historique créé
    """
    historique = Historique(
        id_acteur=id_acteur,
        action_type=action_type,
        description=description,
        target_id=target_id,
        role_visibility=role_visibility,
        date_creation=datetime.now(timezone.utc)
    )
    
    db.add(historique)
    db.commit()
    db.refresh(historique)
    
    return historique

def create_historique_for_super_admin(
    db: Session,
    id_acteur: int,
    action_type: str,
    description: str,
    target_id: int | None = None
) -> Historique:
    """
    Crée un historique visible uniquement par les Super Admins.
    Utilisé pour les actions comme acceptation/refus d'admin local, gestion d'antennes, etc.
    """
    return create_historique(
        db=db,
        id_acteur=id_acteur,
        action_type=action_type,
        description=description,
        target_id=target_id,
        role_visibility="SUPER_ADMIN"
    )

def create_historique_for_admin_local_super(
    db: Session,
    id_acteur: int,
    action_type: str,
    description: str,
    target_id: int | None = None
) -> Historique:
    """
    Crée un historique visible par les Super Admins et les Admins Locaux.
    Utilisé pour les actions comme gestion de livres, etc.
    """
    return create_historique(
        db=db,
        id_acteur=id_acteur,
        action_type=action_type,
        description=description,
        target_id=target_id,
        role_visibility="ADMIN_LOCAL_SUPER"
    )

def create_historique_global(
    db: Session,
    id_acteur: int,
    action_type: str,
    description: str,
    target_id: int | None = None
) -> Historique:
    """
    Crée un historique visible par tous les admins.
    Utilisé pour les actions comme création de sujets de forum, etc.
    """
    return create_historique(
        db=db,
        id_acteur=id_acteur,
        action_type=action_type,
        description=description,
        target_id=target_id,
        role_visibility="GLOBAL"
    )

def create_historique_user(
    db: Session,
    id_acteur: int,
    action_type: str,
    description: str,
    target_id: int | None = None
) -> Historique:
    """
    Crée un historique visible par l'utilisateur et les admins.
    Utilisé pour les actions comme modification de profil utilisateur, etc.
    """
    return create_historique(
        db=db,
        id_acteur=id_acteur,
        action_type=action_type,
        description=description,
        target_id=target_id,
        role_visibility="USER"
    )
