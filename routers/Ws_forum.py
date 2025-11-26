from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List

# Gestion des connexions actives par sujet
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

manager = ConnectionManager()

# WebSocket route
@router.websocket("/ws/{idSujet}")
async def websocket_endpoint(websocket: WebSocket, idSujet: int):
    idSujet = int(idSujet)
    await manager.connect(websocket, idSujet)
    try:
        while True:
            data = await websocket.receive_json()
            # Ici, tu peux sauvegarder le message en BDD si tu veux
            # puis renvoyer aux autres clients connectés
            await manager.send_message_to_sujet(idSujet, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket, idSujet)


