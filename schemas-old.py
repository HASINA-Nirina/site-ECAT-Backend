from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    mot_de_passe: str
    role: str
    province: str | None = None

class UserLogin(BaseModel):
    email: EmailStr
    mot_de_passe: str
