from fastapi import FastAPI
from routers import auth
from Core.database import engine,Base
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from fastapi.staticfiles import StaticFiles


#CREE LES TABLES
Base.metadata.create_all(bind=engine)

app = FastAPI()


origins = ["*"]
app.add_middleware(
    CORSMiddleware, 
    allow_origins = origins,
    allow_credentials=True ,
    allow_methods= ["*"],
    allow_headers= ["*"],
 )

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

app.include_router(auth.router)

# Pour servir les images uploadées
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")



