from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum
from typing import List, Optional

class UserCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    mot_de_passe: str
    province: str | None = None
    role: str
    statuts: str = "En attente"

class UserLogin(BaseModel):
    email: EmailStr
    mot_de_passe: str

class UserRead(UserCreate):
    id: int

    class config:
        orm_mode = True

class AdminUpdateStatus(BaseModel):
    statuts: str
class AdminLocalBase(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    province: str
    statuts: str
    image: Optional[str] = None
class EtudiantOut(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
class Province(BaseModel):
    province:str
    
class UserResponse(BaseModel):
    nom: str
    prenom: str
    email: str
    province: str
class EtudiantResponse(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    province: str

class EmailRequest(BaseModel):
    email: EmailStr

class SendOTPRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    code: str

class ChangePassword(BaseModel):
    id: int 
    mot_de_passe: str

class UserReadLocal(BaseModel):
      province: str

     #FORMATION#
class FormationBase(BaseModel):
    titre: str
    description: str
    image: Optional[str] = None

class FormationCreate(FormationBase):
    pass

class FormationUpdate(FormationBase):
    pass

class FormationResponse(FormationBase):
    idFormation: int
    date_creation: datetime

class UserUpdate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
class PasswordVerify(BaseModel):
    id: int
    mot_de_passe: str 

#########################Paiement################################
class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PaiementResponse(BaseModel):
    idPaiement: int
    idUtilisateur: int
    idLivre: int
    montant: float
    operateur: str
    reference: str
    status: PaymentStatus
    date_creation: datetime
    date_mise_a_jour: datetime


    ################################livre################################
class LivreCreate(BaseModel):
    titre: str
    auteur: str
    image: str | None = None
    urlPdf: str | None = None  
    idFormation: int
    description: str | None = ""
    prix: float = 0
class LivreBase(BaseModel):
    titre: str
    auteur: str | None = None
    urlPdf: str
    idFormation: int | None = None
    description: str | None = None


class LivreUpdate(BaseModel):
    titre: str | None = None
    auteur: str | None = None
    urlPdf: str | None = None
class LivreDebloqueResponse(BaseModel):
     id: int
     title: str
     author: str
     image: str
class   LivreResponse(LivreBase):
    idLivre: int
class LivreRead(BaseModel):
    idFormation: int
class LivreDebloque(BaseModel):
    idUser: int
    idLivre: int
    canAccess: bool

class UserLivreAccessCheck(BaseModel):
    idUser: int
    idLivre: int

###################Forum################

class MessageCreate(BaseModel):
    idSender: int
    idSujet: int
    contenu: str
    idParentMessage: Optional[int] = None

class MessageOut(BaseModel):
    idMessage: int
    idSender: int
    contenu: str
    date_creation: datetime
    idParentMessage: Optional[int]

    class Config:
        orm_mode = True

class SujetOut(BaseModel):
    idSujet: int
    titre: str
    idCreateur: int
    date_creation: datetime
    messages: List[MessageOut] = []

    class config:
        orm_mode = True
        model_config = {
    "from_attributes": True
}

