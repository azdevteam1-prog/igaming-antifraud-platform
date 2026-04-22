from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionFilter,
    TransactionStats
)
from ..models import Transaction, Player
from ..core.security import get_current_user

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)


@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new transaction record."""
    
    # Verify player exists
    player = db.query(Player).filter(Player.id == transaction.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    player_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get transactions with optional filters."""
    
    query = db.query(Transaction)
    
    if player_id:
        query = query.filter(Transaction.player_id == player_id)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)
    if start_date:
        query = query.filter(Transaction.created_at >= start_date)
    if end_date:
        query = query.filter(Transaction.created_at <= end_date)
    
    transactions = query.offset(skip).limit(limit).all()
    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific transaction by ID."""
    
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction


@router.get("/player/{player_id}/stats", response_model=TransactionStats)
async def get_player_transaction_stats(
    player_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get transaction statistics for a player."""
    
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    transactions = db.query(Transaction).filter(
        Transaction.player_id == player_id,
        Transaction.created_at >= start_date
    ).all()
    
    total_deposits = sum(t.amount for t in transactions if t.transaction_type == 'deposit')
    total_withdrawals = sum(t.amount for t in transactions if t.transaction_type == 'withdrawal')
    total_bets = sum(t.amount for t in transactions if t.transaction_type == 'bet')
    total_wins = sum(t.amount for t in transactions if t.transaction_type == 'win')
    
    return {
        'player_id': player_id,
        'period_days': days,
        'total_transactions': len(transactions),
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_bets': total_bets,
        'total_wins': total_wins,
        'net_position': total_deposits - total_withdrawals + total_wins - total_bets
    }


@router.get("/suspicious/high-value")
async def get_high_value_transactions(
    threshold: float = Query(1000.0, ge=0),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get high-value transactions that may require review."""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    transactions = db.query(Transaction).filter(
        Transaction.amount >= threshold,
        Transaction.created_at >= start_date
    ).order_by(Transaction.amount.desc()).all()
    
    return {
        'threshold': threshold,
        'period_days': days,
        'count': len(transactions),
        'transactions': transactions
    }
