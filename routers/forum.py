from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_
from Core.database import get_db
from Controllers.forum_contronllers import get_user_details,ajouter_message, get_all_sujets, get_sujet_by_id, create_sujet
from schemas.user_schemas import MessageCreate,SujetOut,SujetResponse,MessageResponse
from models.models import Message,Sujet, User
from typing import List, Optional, Union
from .auth import get_current_user 
from datetime import datetime, timezone

from fastapi import File, UploadFile, Form
from typing import Optional
import os
import time
from fastapi import APIRouter, Form, File, UploadFile, Depends
from typing import Optional
from sqlalchemy.orm import Session
from Core.database import get_db
from models.models import Message
from fastapi.responses import FileResponse
import os
import urllib.parse

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List


router = APIRouter(prefix="/forum", tags=["Forum"])


@router.post("/ajouter", response_model=MessageResponse)
async def add_message(data: MessageCreate, db: Session = Depends(get_db)):
    message = await ajouter_message(db, data)
    return message

@router.get("/sujet", response_model=list[SujetOut])
def list_sujets(db: Session = Depends(get_db)):
    return get_all_sujets(db)

@router.post("/sujets", response_model=SujetResponse)
async def create_new_sujet(
    titre: str = Form(...),
    idCreateur: int = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    return await create_sujet(db, titre, idCreateur, image)


@router.get("/ReadSujet/{idUser}", response_model=List[SujetResponse])
def read_sujet_by_user(
    idUser: int, 
    db: Session = Depends(get_db),
):
    # Récupérer l'utilisateur
    user = db.query(User).filter(User.id == idUser).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    sujets = []
    # ROLE : ADMIN
    if user.role.lower() == "admin":
        sujets = db.query(Sujet).filter(
            Sujet.province.in_(["admin", "public"])
        ).order_by(Sujet.date_creation.desc()).all()
    # ROLE : ADMIN LOCAL
    elif user.role.lower() == "admin local":
        sujets = db.query(Sujet).filter(
            Sujet.province.in_(["admin", "public", user.province])
        ).order_by(Sujet.date_creation.desc()).all()
    # ROLE : ETUDIANT
    else:
        sujets = db.query(Sujet).filter(
            Sujet.province.in_(["public", user.province])
        ).order_by(Sujet.date_creation.desc()).all()

    return sujets

@router.post("/NewSujet")
async def create_sujet(
    titre: str = Form(...),
    idCreateur: int = Form(...),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    try:
        # Gestion de l'image
        image_filename = None
        if image:
            timestamp = int(datetime.now().timestamp())
            ext = os.path.splitext(image.filename)[1]
            image_filename = f"{timestamp}_{image.filename}"
            file_path = os.path.join(UPLOAD_DIR, image_filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
        
        new_sujet = Sujet(
            titre=titre,
            idCreateur=idCreateur,
            image=image_filename,
            province="public",
            date_creation=datetime.now(timezone.utc)
        )
        db.add(new_sujet)
        db.commit()
        db.refresh(new_sujet)
        return new_sujet
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{idSujet}", response_model=SujetOut)
def show_sujet(idSujet: int, db: Session = Depends(get_db)):
    sujet = get_sujet_by_id(db, idSujet)
    if not sujet:
        raise HTTPException(status_code=404, detail="Sujet non trouvé")
    return sujet
from fastapi import WebSocket, WebSocketDisconnect
from Core.database import SessionLocal
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, idSujet: int):
        await websocket.accept()
        if idSujet not in self.active_connections:
            self.active_connections[idSujet] = []
        self.active_connections[idSujet].append(websocket)

    def disconnect(self, websocket: WebSocket, idSujet: int):
        if idSujet in self.active_connections:
            self.active_connections[idSujet].remove(websocket)

    async def send_message_to_sujet(self, idSujet: int, message: dict):
        if idSujet in self.active_connections:
            for connection in self.active_connections[idSujet]:
                await connection.send_json(message)

# Crée l’instance globale du manager
manager = ConnectionManager()

@router.post("/ajouter_message")
async def ajouter_message(
    idSender: int = Form(...),
    idSujet: int = Form(...),
    contenu: str = Form(""),
    idParentMessage: Optional[int] = Form(None),
    fichier: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Créer le dossier uploads s'il n'existe pas
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    fichier_path = None
    if fichier is not None:  
        ext = os.path.splitext(fichier.filename)[1]
        original_name = os.path.splitext(fichier.filename)[0]
        ext = os.path.splitext(fichier.filename)[1]
        save_name = f"{original_name}_{idSender}_{int(time.time())}{ext}"
        fichier_path = os.path.join(upload_dir, save_name)
        with open(fichier_path, "wb") as f:
            f.write(await fichier.read())

    
    new_message = Message(
    idSender=idSender,
    idSujet=idSujet,
    contenu=contenu,
    fichier=save_name if fichier is not None else None, 
    idParentMessage=idParentMessage
)


    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return {"message": "Message envoyé", "data": new_message}


@router.websocket("/ws/{idSujet}")
async def websocket_endpoint(websocket: WebSocket, idSujet: int):
    idSujet = int(idSujet)

    # Ouvrir une session DB ici car Depends ne fonctionne pas avec WS
    db = SessionLocal()  # ou async avec SQLAlchemy async si tu utilises async
    try:
        await manager.connect(websocket, idSujet)

        # 3️⃣ Envoyer les messages existants du sujet au client
        messages_existants = db.query(Message).filter(Message.idSujet == idSujet).all()
        for m in messages_existants:
            sender_details = db.query(User).filter(User.id == m.idSender).first()
            full_message_data = {
                "id": m.idMessage,
                "contenu": m.contenu,
                "fichier": m.fichier,
                "idSujet": m.idSujet,
                "idSender": m.idSender,
                "date_creation": m.date_creation.isoformat(),
                "idParentMessage": m.idParentMessage,
                "sender": {
                    "id": sender_details.id,
                    "nom": sender_details.nom,
                    "prenom": sender_details.prenom,
                    "email": sender_details.email,
                    "image": sender_details.image,
                }
            }
            await websocket.send_json(full_message_data)  # envoie chaque message existant au client

        while True:
            data = await websocket.receive_json()
            id_sender = data.get("idSender")
            if not id_sender:
                continue

            sender_details = await get_user_details(db, id_sender)

            full_message_data = {
                **data,
                "date_creation": datetime.now(timezone.utc).isoformat(),
                "sender": {
                    "id": sender_details.id,
                    "nom": sender_details.nom,
                    "prenom": sender_details.prenom,
                    "email": sender_details.email,
                    "image": sender_details.image,
                }
            }

            # 5️⃣ Diffuser à tous les clients du même sujet
            await manager.send_message_to_sujet(idSujet, full_message_data)

    except WebSocketDisconnect:
        manager.disconnect(websocket, idSujet)

    finally:
        db.close()



@router.get("/filesdownload/{filename}")
def download_file(filename: str):
    upload_dir = "uploads"
    filename = urllib.parse.unquote(filename)
    filename = os.path.basename(filename)
    
    file_path = os.path.join(upload_dir, filename)
    print(file_path)  
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)
