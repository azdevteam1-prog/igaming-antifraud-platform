from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.core.database import get_db
from app.models.player import Player
from app.models.transaction import Transaction
from app.models.alert import Alert
from app.schemas.player import PlayerOut, PlayerUpdate
from app.schemas.transaction import TransactionOut
from typing import List
from datetime import datetime, timedelta

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/", response_model=List[PlayerOut])
async def list_players(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).order_by(desc(Player.risk_score)).limit(200))
    return result.scalars().all()

@router.get("/{player_id}", response_model=PlayerOut)
async def get_player(player_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar()
    if not player:
        raise HTTPException(404, "Player not found")
    return player

@router.put("/{player_id}", response_model=PlayerOut)
async def update_player(player_id: str, data: PlayerUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar()
    if not player:
        raise HTTPException(404, "Player not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(player, k, v)
    await db.commit()
    await db.refresh(player)
    return player

@router.get("/{player_id}/profile")
async def get_player_profile(player_id: str, db: AsyncSession = Depends(get_db)):
    player_result = await db.execute(select(Player).where(Player.id == player_id))
    player = player_result.scalar()
    if not player:
        raise HTTPException(404, "Player not found")
    
    # Get transaction stats
    tx_result = await db.execute(
        select(
            func.count(Transaction.id).label('total_count'),
            func.sum(Transaction.amount).label('total_volume'),
            func.avg(Transaction.amount).label('avg_amount')
        ).where(Transaction.player_id == player_id)
    )
    tx_stats = tx_result.first()
    
    # Get recent alerts
    alerts_result = await db.execute(
        select(Alert).where(Alert.player_id == player_id).order_by(desc(Alert.created_at)).limit(10)
    )
    recent_alerts = alerts_result.scalars().all()
    
    return {
        "player": player,
        "transaction_stats": {
            "total_count": tx_stats.total_count or 0,
            "total_volume": float(tx_stats.total_volume or 0),
            "avg_amount": float(tx_stats.avg_amount or 0)
        },
        "recent_alerts": [{
            "id": alert.id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "created_at": alert.created_at.isoformat()
        } for alert in recent_alerts]
    }

@router.get("/{player_id}/sessions")
async def get_player_sessions(player_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    # Mock session data - in production would query session model
    player_result = await db.execute(select(Player).where(Player.id == player_id))
    player = player_result.scalar()
    if not player:
        raise HTTPException(404, "Player not found")
    
    return {
        "player_id": player_id,
        "sessions": [
            {
                "session_id": f"sess_{i}",
                "ip_address": f"192.168.{i}.{i}",
                "device_id": player.device_id,
                "started_at": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                "duration_minutes": 30 + i * 5
            } for i in range(min(limit, 10))
        ]
    }

@router.get("/{player_id}/devices")
async def get_player_devices(player_id: str, db: AsyncSession = Depends(get_db)):
    player_result = await db.execute(select(Player).where(Player.id == player_id))
    player = player_result.scalar()
    if not player:
        raise HTTPException(404, "Player not found")
    
    # Mock device data - in production would query device fingerprint model
    return {
        "player_id": player_id,
        "devices": [
            {
                "device_id": player.device_id,
                "fingerprint": player.device_fingerprint or "unknown",
                "first_seen": player.created_at.isoformat(),
                "last_seen": datetime.utcnow().isoformat(),
                "ip_addresses": [player.ip_address],
                "risk_score": player.risk_score
            }
        ]
    }

@router.get("/{player_id}/transactions", response_model=List[TransactionOut])
async def get_player_transactions(player_id: str, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Transaction).where(Transaction.player_id == player_id).order_by(desc(Transaction.created_at)).limit(limit)
    )
    return result.scalars().all()

@router.post("/{player_id}/flag")
async def flag_player(player_id: str, reason: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar()
    if not player:
        raise HTTPException(404, "Player not found")
    
    player.status = "flagged"
    player.risk_score = min(player.risk_score + 20, 100)
    await db.commit()
    
    return {"ok": True, "player_id": player_id, "status": "flagged", "reason": reason}

@router.post("/{player_id}/block")
async def block_player(player_id: str, reason: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar()
    if not player:
        raise HTTPException(404, "Player not found")
    
    player.status = "blocked"
    await db.commit()
    
    return {"ok": True, "player_id": player_id, "status": "blocked", "reason": reason}
