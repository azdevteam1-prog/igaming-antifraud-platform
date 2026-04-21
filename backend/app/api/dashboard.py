from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.models.player import Player
from app.models.transaction import Transaction
from app.models.alert import Alert
from app.models.rule import Rule
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    last24h = now - timedelta(hours=24)

    total_players = (await db.execute(select(func.count()).select_from(Player))).scalar()
    total_txs = (await db.execute(select(func.count()).select_from(Transaction))).scalar()
    flagged_txs = (await db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.status.in_(["flagged", "review", "hold"]))
    )).scalar()
    open_alerts = (await db.execute(
        select(func.count()).select_from(Alert).where(Alert.status == "open")
    )).scalar()
    critical_alerts = (await db.execute(
        select(func.count()).select_from(Alert).where(Alert.severity == "Critical")
    )).scalar()
    high_risk_players = (await db.execute(
        select(func.count()).select_from(Player).where(Player.risk_label.in_(["High", "Critical"]))
    )).scalar()
    txs_24h = (await db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.created_at >= last24h)
    )).scalar()
    volume_result = await db.execute(select(func.sum(Transaction.amount)).select_from(Transaction))
    total_volume = volume_result.scalar() or 0

    return {
        "total_players": total_players,
        "total_transactions": total_txs,
        "flagged_transactions": flagged_txs,
        "open_alerts": open_alerts,
        "critical_alerts": critical_alerts,
        "high_risk_players": high_risk_players,
        "transactions_24h": txs_24h,
        "total_volume": round(total_volume, 2),
    }
