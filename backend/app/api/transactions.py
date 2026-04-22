from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionOut
from app.ml.risk_model import RiskScorer
from typing import Optional, List
from datetime import datetime

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
    raise HTTPException(status_code=404, detail="Transaction not found")

@router.post("/{tx_id}/flag")
async def flag_transaction(
    tx_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Transaction).where(Transaction.id == tx_id))
    tx = result.scalar()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    tx.risk_label = "high"
    tx.status = "flagged"
    tx.notes = f"Flagged: {reason} at {datetime.utcnow()}"
    await db.commit()
    return {"ok": True, "id": tx_id, "action": "flagged", "reason": reason}

@router.post("/{tx_id}/block")
async def block_transaction(
    tx_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Transaction).where(Transaction.id == tx_id))
    tx = result.scalar()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    tx.status = "blocked"
    tx.notes = f"Blocked: {reason} at {datetime.utcnow()}"
    await db.commit()
    return {"ok": True, "id": tx_id, "action": "blocked", "reason": reason}

@router.post("/{tx_id}/approve")
async def approve_transaction(
    tx_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Transaction).where(Transaction.id == tx_id))
    tx = result.scalar()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    tx.status = "approved"
    tx.risk_label = "low"
    await db.commit()
    return {"ok": True, "id": tx_id, "action": "approved"}

@router.post("/{tx_id}/rescore")
async def rescore_transaction(
    tx_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Transaction).where(Transaction.id == tx_id))
    tx = result.scalar()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    scorer = RiskScorer()
    
    # Get player transaction history
    player_txs = await db.execute(
        select(Transaction).where(Transaction.player_id == tx.player_id).order_by(desc(Transaction.created_at)).limit(100)
    )
    tx_history = player_txs.scalars().all()
    
    # Calculate risk score
    features = {
        'amount': float(tx.amount),
        'tx_count_24h': sum(1 for t in tx_history if (datetime.utcnow() - t.created_at).total_seconds() < 86400),
        'avg_amount': sum(float(t.amount) for t in tx_history) / len(tx_history) if tx_history else 0,
        'failed_count': sum(1 for t in tx_history if t.status == 'failed'),
        'chargeback_count': sum(1 for t in tx_history if t.status == 'chargeback')
    }
    
    risk_score, risk_label = scorer.predict(features)
    
    tx.risk_score = risk_score
    tx.risk_label = risk_label
    await db.commit()
    
    return {
        "ok": True,
        "id": tx_id,
        "risk_score": risk_score,
        "risk_label": risk_label,
        "features": features
    }
