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
    province: str
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
    id: int
    nom: str
    prenom: str
    email: EmailStr
    province: str

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    mot_de_passe: str

class UserRead(UserCreate):
    id: int

    class config:
        orm_mode = True

class UserRead(UserCreate):
    id: int
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

class FormationResponse(BaseModel):
    idFormation: int
    titre: str
    description: str
    image: str | None
class UserUpdate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
class PasswordVerify(BaseModel):
    id: int
    mot_de_passe: str 

#########################Paiement################################
class PaymentStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

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
    contact: str  
    montant: float
    operateur: str 
    reference: str 
    canAccess: bool = True

class UserLivreAccessCheck(BaseModel):
    idUser: int
    idLivre: int

###################Forum################
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
    image: str | None = None
    messages: List[MessageOut] = []


    # nouveau champ
class SujetResponse(BaseModel):
    idSujet: int
    titre: str
    image: str | None = None  
    date_creation: datetime
    isCreator: Optional[bool] = None 
    class Config:
        orm_mode = True
        from_attributes = True
   
class SenderSchema(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    image: Optional[str] = None 
class MessageSchema(BaseModel):
    idMessage: int
    idSender: int
    idSujet: int
    contenu: str
    fichier: Optional[str] = None
    date_creation: datetime
    idParentMessage: Optional[int] = None
class MessageCreate(BaseModel):
    idSujet: int
    idCreateur: int
    content: str
    fileUrl: str | None = None

class MessageResponse(BaseModel):
    idMessage: int
    idSujet: int
    idCreateur: int
    content: str
    fileUrl: str | None
    created_at: datetime

    class Config:
        orm_mode = True    
    sender: SenderSchema

    class Config:
        from_attributes = True
    class config:
        orm_mode = True
        model_config = {
    "from_attributes": True
}

class AntenneBase(BaseModel):
    province: str

class AntenneCreate(AntenneBase):
    pass

class AntenneUpdate(AntenneBase):
    pass

class AntenneOut(AntenneBase):
    id: int

    class Config:
        orm_mode = True

###################Historique################
class HistoriqueBase(BaseModel):
    id_acteur: int
    action_type: str
    description: str
    target_id: Optional[int] = None
    role_visibility: str  # 'SUPER_ADMIN', 'ADMIN_LOCAL_SUPER', 'GLOBAL', 'USER'

class HistoriqueCreate(HistoriqueBase):
    pass

class HistoriqueResponse(BaseModel):
    id: int
    id_acteur: int
    action_type: str
    description: str
    target_id: Optional[int] = None
    role_visibility: str
    date_creation: datetime
    acteur_nom: Optional[str] = None
    acteur_prenom: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True


