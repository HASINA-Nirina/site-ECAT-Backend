# backend/create_tables.py
from Core.database import Base, engine
from models import User

Base.metadata.create_all(bind=engine)
print("Tables créées avec succès !")
