import sys, os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI
from routers import auth, formation, paiement, livre, forum
from Core.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from Core.database import SessionLocal
from models.models import User,Sujet
from Core.security import hash_password
from fastapi.staticfiles import StaticFiles

Base.metadata.create_all(bind=engine)
       

async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # Création de l'admin si nécessaire
        admin_email = "admin@ecat.mg"
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
            statuts="Actif"
            )
            db.add(admin_user)
            db.commit()
            print("✅ etudiant créé")

        # Création du sujet Administratif si nécessaire
        admin_sujet = db.query(Sujet).filter(Sujet.titre == "Administratif").first()
        if not admin_sujet:
            admin_sujet = Sujet(
                titre="Administratif",
                idCreateur=2
            )
            db.add(admin_sujet)
            db.commit()  
            db.refresh(admin_sujet)
            print("✅ Sujet Admin créé")
        
        yield

    finally:
        db.close()


app = FastAPI(lifespan=lifespan)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(formation.router)
app.include_router(paiement.router)
app.include_router(livre.router)
app.include_router(forum.router)
