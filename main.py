import sys, os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI
from routers import auth
from Core.database import engine,Base
from fastapi.middleware.cors import CORSMiddleware
from Core import database
from sqlalchemy.orm import Session
from Core.database import SessionLocal
from models.models import User
import bcrypt

   

import psycopg2

#CREE LES TABLES
database.Base.metadata.create_all(bind=database.engine)


async def lifespan(app: FastAPI):
    database.Base.metadata.create_all(bind=database.engine)
    db: Session = SessionLocal()
    admin_email = "admin@ecat.mg"

    admin = db.query(User).filter(User.email == admin_email).first()
    if not admin:
        hashed_pw = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin_user = User(
            nom="Admin",
            prenom="Principal",
            email=admin_email,
            mot_de_passe=hashed_pw,
            role="admin",
            province=None,
            status="actif"
        )
        db.add(admin_user)
        db.commit()
        print("✅ Admin créé")
    else:
        print("ℹ️ Admin existe déjà")
    db.close()

    print("✅ Admin initialisé")
    yield
    print("🛑 Fermeture de l'application")

app = FastAPI(lifespan=lifespan)



origins = ["*"]
app.add_middleware(
    CORSMiddleware, 
    allow_origins = origins,
    allow_credentials=True ,
    allow_methods= ["*"],
    allow_headers= ["*"],
 )
app.include_router(auth.router)
