from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from Core.database import get_db
from Controllers.historique_controller import get_historiques_by_role
from models.models import User
from Core.config import SECRET_KEY, ALGORITHM
import jwt
from typing import Optional

router = APIRouter(prefix="/admin/super", tags=["Rapports"])

@router.get("/rapports")
def get_rapports(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    Endpoint pour récupérer les historiques/rapports avec pagination.
    Filtre les historiques en fonction du rôle de l'utilisateur connecté.
    """
    # Récupérer le token depuis les cookies ou le header Authorization
    token = request.cookies.get("token")
    if not token:
        # Essayer depuis le header Authorization
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            raise HTTPException(status_code=401, detail="Token manquant")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        
        if not user_email:
            raise HTTPException(status_code=401, detail="Token invalide")
        
        # Récupérer l'utilisateur depuis la base de données
        current_user = db.query(User).filter(User.email == user_email).first()
        
        if not current_user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        
        # Vérifier que l'utilisateur est un admin (Super Admin ou Admin Local)
        if current_user.role not in ["admin", "Admin Local"]:
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs.")
        
        # Valider la pagination
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        
        # Récupérer les historiques
        historiques, total = get_historiques_by_role(
            db=db,
            current_user=current_user,
            page=page,
            page_size=page_size
        )
        
        # Calculer le nombre total de pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        return {
            "historiques": historiques,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages
            }
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

