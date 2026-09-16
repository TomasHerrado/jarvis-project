from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Jarvis Core API")

# Tauri corre el frontend en un origen local distinto al del backend,
# así que necesitamos habilitar CORS para desarrollo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción esto se restringe
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "jarvis-core"}


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Por ahora, eco: confirma que el canal funciona en los dos sentidos
            await manager.broadcast({"type": "echo", "payload": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)