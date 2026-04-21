from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.player import Player
from app.models.transaction import Transaction
from app.models.alert import Alert
from app.schemas.player import PlayerOut, PlayerUpdate
from app.schemas.transaction import TransactionOut
from app.schemas.alert import AlertOut
from app.services.link_analysis import get_player_graph, rebuild_entity_links
from typing import List

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/", response_model=List[PlayerOut])
async def list_players(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).order_by(desc(Player.risk_score)).limit(200))
    return result.scalars().all()

@router.get("/{player_id}", response_model=PlayerOut)
async def get_player(player_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.id == player_id))
    p = result.scalar()
    if not p:
        raise HTTPException(404, "Player not found")
    return p

@router.get("/{player_id}/transactions", response_model=List[TransactionOut])
async def player_transactions(player_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.player_id == player_id)
        .order_by(desc(Transaction.created_at))
        .limit(100)
    )
    return result.scalars().all()

@router.get("/{player_id}/alerts", response_model=List[AlertOut])
async def player_alerts(player_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Alert).where(Alert.player_id == player_id).order_by(desc(Alert.created_at)).limit(50)
    )
    return result.scalars().all()

@router.get("/{player_id}/graph")
async def player_graph(player_id: str, db: AsyncSession = Depends(get_db)):
    await rebuild_entity_links(
        (await db.execute(select(Player).where(Player.id == player_id))).scalar(),
        db
    )
    return await get_player_graph(player_id, db)

@router.patch("/{player_id}")
async def update_player(player_id: str, data: PlayerUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.id == player_id))
    p = result.scalar()
    if not p:
        raise HTTPException(404, "Player not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    await db.commit()
    return {"ok": True}
