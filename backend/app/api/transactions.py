from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionOut
from typing import Optional, List

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("/", response_model=List[TransactionOut])
async def list_transactions(
    tx_type: Optional[str] = None,
    status: Optional[str] = None,
    risk_label: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    q = select(Transaction).order_by(desc(Transaction.created_at))
    if tx_type:
        q = q.where(Transaction.tx_type == tx_type)
    if status:
        q = q.where(Transaction.status == status)
    if risk_label:
        q = q.where(Transaction.risk_label == risk_label)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()

@router.get("/deposits", response_model=List[TransactionOut])
async def live_deposits(
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    q = select(Transaction).where(Transaction.tx_type == "deposit").order_by(desc(Transaction.created_at))
    if status:
        q = q.where(Transaction.status == status)
    result = await db.execute(q.limit(limit))
    return result.scalars().all()

@router.get("/withdrawals", response_model=List[TransactionOut])
async def live_withdrawals(
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    q = select(Transaction).where(Transaction.tx_type == "withdrawal").order_by(desc(Transaction.created_at))
    if status:
        q = q.where(Transaction.status == status)
    result = await db.execute(q.limit(limit))
    return result.scalars().all()

@router.patch("/{tx_id}/status")
async def update_tx_status(
    tx_id: str,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Transaction).where(Transaction.id == tx_id))
    tx = result.scalar()
    if tx:
        tx.status = status
        await db.commit()
    return {"ok": True, "id": tx_id, "status": status}
