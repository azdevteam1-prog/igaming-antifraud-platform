from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio

router = APIRouter(tags=["websocket"])

class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        data = json.dumps(message, default=str)
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)

manager = ConnectionManager()

@router.websocket("/ws/transactions")
async def ws_transactions(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(30)  # keepalive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_transaction(tx):
    await manager.broadcast({
        "event": "new_transaction",
        "data": {
            "id": tx.id,
            "player_id": tx.player_id,
            "tx_type": tx.tx_type,
            "amount": tx.amount,
            "currency": tx.currency,
            "payment_method": tx.payment_method,
            "status": tx.status,
            "risk_score": tx.risk_score,
            "risk_label": tx.risk_label,
            "country": tx.country,
            "rule_hits": tx.rule_hits,
            "created_at": str(tx.created_at),
        }
    })
