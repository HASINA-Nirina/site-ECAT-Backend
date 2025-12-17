from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from Core.database import get_db
from Controllers.stats_controller import get_dashboard_stats
from Controllers.user_controllers import get_current_user
from models.models import User

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("/dashboard")
def dashboard_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint pour récupérer les statistiques du dashboard Admin Local.
    Retourne les KPIs filtrés par la province de l'admin connecté.
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
    
    # Décoder le token pour obtenir l'utilisateur
    from Core.config import SECRET_KEY, ALGORITHM
    import jwt
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        
        if not user_email:
            raise HTTPException(status_code=401, detail="Token invalide")
        
        # Récupérer l'utilisateur depuis la base de données
        current_user = db.query(User).filter(User.email == user_email).first()
        
        if not current_user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        
        # Vérifier que c'est un Admin Local
        if current_user.role != "Admin Local":
            raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur local.")
        
        # Récupérer les statistiques
        stats = get_dashboard_stats(db, current_user)
        
        return stats
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

