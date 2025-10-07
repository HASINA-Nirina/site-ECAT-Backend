from fastapi import FastAPI
from routers import auth
from Core.database import engine,Base

#CREE LES TABLES
Base.metadata.create_all(bind=engine)
print("table cree")
app = FastAPI()

app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur Site-ECAT Backend"}
