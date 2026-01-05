import sys, os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI
from routers import auth, formation, paiement, livre, forum, antenne, stats, student, rapports
from routers import dashboard_router 
from Core.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from Core.database import SessionLocal
from models.models import User, Sujet
from Core.security import hash_password
from fastapi.staticfiles import StaticFiles
import os
# En production, vous définirez cette variable sur votre serveur
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

Base.metadata.create_all(bind=engine, checkfirst=True)


async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # --- Création de l'admin super si nécessaire ---
        admin_email = "jeandedieuhasinirina82@gmail.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            hashed_pw = hash_password("admin123")
            admin_user = User(
            nom="Admin",
            prenom="Principal",
            email=admin_email,
            mot_de_passe=hashed_pw,
            role="admin",
            province=None,
            statuts="Actif")

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
                theme="light",)
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print("✅ Admin super créé")

        # --- Création du sujet Administratif si nécessaire ---
        admin_id = admin.id if admin else admin_user.id
        admin_sujet = db.query(Sujet).filter(Sujet.titre == "Administratif").first()
        if not admin_sujet:
            admin_sujet = Sujet(
                titre="Administratif",
                idCreateur=admin_id,
                province="admin"
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
# --- CORS Middleware ---
origins = [ 
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://ecat-taratra.vercel.app", # Retrait du slash final ici
]

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
app.include_router(antenne.router)
app.include_router(stats.router)
app.include_router(student.router)
app.include_router(rapports.router)
app.include_router(dashboard_router.router)

# --- Pour servir les images uploadées ---
required_dirs = ["upload", "uploads"]

for directory in required_dirs:
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"✅ Dossier créé : {directory}")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/upload", StaticFiles(directory="upload"), name="upload")
