import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Fix import path
sys.path.append(os.path.dirname(__file__))

# Imports internes
from Core.database import Base, engine, SessionLocal
from Core.security import hash_password
from models.models import User, Sujet

from routers import (
    auth,
    formation,
    paiement,
    livre,
    forum,
    antenne,
    stats,
    student,
    rapports,
    dashboard_router,
)

# ======================================================
# CONFIG APP
# ======================================================

app = FastAPI(
    title="ECAT Backend API",
    version="1.0.0",
)

# ======================================================
# CORS (DOIT ÊTRE ICI, AVANT TOUT)
# ======================================================

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://ecat-taratra.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)
# ======================================================
# STARTUP (REMPLACE LIFESPAN)
# ======================================================

@app.on_event("startup")
async def startup():
    # Création des tables
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # --------- ADMIN SUPER ---------
        admin_email = "jeandedieuhasinirina82@gmail.com"
        admin = db.query(User).filter(User.email == admin_email).first()

        if not admin:
            admin_user = User(
                nom="HASINIRINA",
                prenom="Yannick",
                email=admin_email,
                mot_de_passe=hash_password("admin123"),
                role="admin",
                province="Fianarantsoa",
                image=None,
                statuts="Actif",
                theme="light",
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            admin = admin_user
            print("✅ Admin super créé")

        # --------- SUJET ADMINISTRATIF ---------
        sujet = db.query(Sujet).filter(Sujet.titre == "Administratif").first()
        if not sujet:
            sujet = Sujet(
                titre="Administratif",
                idCreateur=admin.id,
                province="admin",
            )
            db.add(sujet)
            db.commit()
            print("✅ Sujet Administratif créé")

    finally:
        db.close()

# ======================================================
# ROUTES DE TEST
# ======================================================

@app.get("/")
def root():
    return {"message": "ECAT Backend opérationnel"}

# ======================================================
# ROUTERS
# ======================================================

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

# ======================================================
# STATIC FILES
# ======================================================

for folder in ["upload", "uploads"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.mount("/upload", StaticFiles(directory="upload"), name="upload")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
