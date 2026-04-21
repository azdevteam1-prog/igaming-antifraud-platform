"""
Analytics API Router for iGaming Anti-Fraud Platform
Provides aggregated fraud statistics, trend analysis, and
operational KPI endpoints for the dashboard and reporting.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta
from typing import Optional, List
from app.core.database import get_db
from app.models.transaction import Transaction
from app.models.alert import Alert
from app.models.player import Player
from app.models.rule import Rule

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _days_range(days: int) -> datetime:
    return datetime.utcnow() - timedelta(days=days)


# ---------------------------------------------------------------------------
# Transaction volume & fraud rate over time
# ---------------------------------------------------------------------------

@router.get("/fraud-rate")
async def get_fraud_rate(
    days: int = Query(default=7, ge=1, le=90, description="Lookback window in days"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return daily transaction counts and fraud rate for the last N days.
    """
    since = _days_range(days)

    total_result = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.created_at >= since)
    )
    total = total_result.scalar() or 0

    flagged_result = await db.execute(
        select(func.count(Transaction.id))
        .where(
            Transaction.created_at >= since,
            Transaction.status == "flagged",
        )
    )
    flagged = flagged_result.scalar() or 0

    fraud_rate = round((flagged / total * 100) if total > 0 else 0.0, 2)

    return {
        "period_days": days,
        "total_transactions": total,
        "flagged_transactions": flagged,
        "fraud_rate_pct": fraud_rate,
    }


# ---------------------------------------------------------------------------
# Top risky players
# ---------------------------------------------------------------------------

@router.get("/top-risky-players")
async def get_top_risky_players(
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Return players sorted by risk score descending.
    """
    result = await db.execute(
        select(
            Player.id,
            Player.username,
            Player.risk_score,
            Player.multi_account_flag,
            Player.sanctions_flag,
            Player.kyc_verified,
        )
        .order_by(Player.risk_score.desc())
        .limit(limit)
    )
    rows = result.fetchall()
    return [
        {
            "id": str(r.id),
            "username": r.username,
            "risk_score": r.risk_score,
            "multi_account_flag": r.multi_account_flag,
            "sanctions_flag": r.sanctions_flag,
            "kyc_verified": r.kyc_verified,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Alert breakdown by rule
# ---------------------------------------------------------------------------

@router.get("/alerts-by-rule")
async def get_alerts_by_rule(
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """
    Return alert count grouped by triggered rule code.
    """
    since = _days_range(days)
    result = await db.execute(
        select(Alert.rule_code, func.count(Alert.id).label("count"))
        .where(Alert.created_at >= since)
        .group_by(Alert.rule_code)
        .order_by(text("count DESC"))
    )
    rows = result.fetchall()
    return [{"rule_code": r.rule_code, "alert_count": r.count} for r in rows]


# ---------------------------------------------------------------------------
# Volume by transaction type
# ---------------------------------------------------------------------------

@router.get("/volume-by-type")
async def get_volume_by_type(
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """
    Return total transaction volume (amount + count) grouped by type.
    """
    since = _days_range(days)
    result = await db.execute(
        select(
            Transaction.tx_type,
            func.count(Transaction.id).label("count"),
            func.sum(Transaction.amount).label("total_amount"),
            func.avg(Transaction.amount).label("avg_amount"),
        )
        .where(Transaction.created_at >= since)
        .group_by(Transaction.tx_type)
    )
    rows = result.fetchall()
    return [
        {
            "tx_type": r.tx_type,
            "count": r.count,
            "total_amount": round(float(r.total_amount or 0), 2),
            "avg_amount": round(float(r.avg_amount or 0), 2),
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Risk score distribution
# ---------------------------------------------------------------------------

@router.get("/risk-distribution")
async def get_risk_distribution(
    db: AsyncSession = Depends(get_db),
):
    """
    Return player count bucketed by risk score range.
    """
    buckets = [
        ("low", 0.0, 0.4),
        ("medium", 0.4, 0.7),
        ("high", 0.7, 1.01),
    ]
    distribution = []
    for label, low, high in buckets:
        result = await db.execute(
            select(func.count(Player.id))
            .where(Player.risk_score >= low, Player.risk_score < high)
        )
        count = result.scalar() or 0
        distribution.append({"bucket": label, "min": low, "max": high, "count": count})
    return distribution


# ---------------------------------------------------------------------------
# Operational KPIs summary
# ---------------------------------------------------------------------------

@router.get("/kpi-summary")
async def get_kpi_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    Return high-level KPI snapshot for the operations dashboard.
    """
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    async def _count(model, *conditions):
        res = await db.execute(select(func.count(model.id)).where(*conditions))
        return res.scalar() or 0

    total_players = await _count(Player)
    active_players_24h = await _count(Player, Player.last_seen >= last_24h)
    total_txn_7d = await _count(Transaction, Transaction.created_at >= last_7d)
    flagged_txn_7d = await _count(
        Transaction,
        Transaction.created_at >= last_7d,
        Transaction.status == "flagged",
    )
    open_alerts = await _count(Alert, Alert.status == "open")
    high_risk_players = await _count(Player, Player.risk_score >= 0.7)

    return {
        "total_players": total_players,
        "active_players_24h": active_players_24h,
        "total_transactions_7d": total_txn_7d,
        "flagged_transactions_7d": flagged_txn_7d,
        "fraud_rate_7d_pct": round(
            (flagged_txn_7d / total_txn_7d * 100) if total_txn_7d else 0.0, 2
        ),
        "open_alerts": open_alerts,
        "high_risk_players": high_risk_players,
        "generated_at": now.isoformat(),
    }
