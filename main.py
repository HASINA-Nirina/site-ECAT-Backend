import sys, os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI
from routers import auth, formation, paiement, livre, forum
from Core.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from Core.database import SessionLocal
from models.models import User, Sujet
from Core.security import hash_password
from fastapi.staticfiles import StaticFiles

# CRÉE LES TABLES
Base.metadata.create_all(bind=engine)

async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # --- Création de l'admin super si nécessaire ---
        admin_email = "jeandedieuhasinirina82@gmail.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            hashed_pw = hash_password("uy:/p1hvfhasinaC")
            admin_user = User(
                nom="HASINIRINA",
                prenom="Yannick",
                email=admin_email,
                mot_de_passe=hashed_pw,
                role="admin",
                province="Fianarantsoa",
                image=None,
                statuts="Actif",
                theme="light",
                
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print("✅ Admin super créé")

        # --- Création du sujet Administratif si nécessaire ---
        # Utilisation de l'ID réel de l'admin
        admin_id = admin.id if admin else admin_user.id
        admin_sujet = db.query(Sujet).filter(Sujet.titre == "Administratif").first()
        if not admin_sujet:
            admin_sujet = Sujet(
                titre="Administratif",
                idCreateur=admin_id
            )
            db.add(admin_sujet)
            db.commit()
            db.refresh(admin_sujet)
            print("✅ Sujet Administratif créé")
        
        yield

    finally:
        db.close()


app = FastAPI(lifespan=lifespan)

# --- CORS Middleware ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware, 
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes de test ---
@app.get("/")
def read_root():
    return {"message": "Bienvenue sur Site-ECAT Backend"}

@app.get("/test-db")
def test_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return {"message": "Connexion OK", "result": result}
    except Exception as e:
        return {"message": "Erreur", "details": str(e)}

# --- Inclusion des routers ---
app.include_router(auth.router)
app.include_router(formation.router)
app.include_router(paiement.router)
app.include_router(livre.router)
app.include_router(forum.router)

# --- Pour servir les images uploadées ---
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
