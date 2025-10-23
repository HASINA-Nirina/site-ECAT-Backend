from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    mot_de_passe: str
    province: str | None = None
    role: str
    province: str
    statut: str = "En attente"

class UserLogin(BaseModel):
    email: EmailStr
    mot_de_passe: str

class UserRead(UserCreate):
    id: int

    class config:
        orm_mode = True

class UserRead(UserCreate):
    id: int

    class config:
        orm_mode = True