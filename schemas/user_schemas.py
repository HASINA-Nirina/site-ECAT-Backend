from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    province : str
    mot_de_passe: str
    role: str
    
    status: str
class EmailRequest(BaseModel):
    email: EmailStr

class SendOTPRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    code: str
class UserLogin(BaseModel):
    email: EmailStr
    mot_de_passe: str

class UserRead(UserCreate):
    id: int

class ChangePassword(BaseModel):
    email:str
    mot_de_passe:str

    class config:
        orm_mode = True
