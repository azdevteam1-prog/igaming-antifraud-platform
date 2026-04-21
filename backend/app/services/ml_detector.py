"""
ML-based Anomaly Detector for iGaming Anti-Fraud Platform
Uses statistical methods and lightweight ML heuristics to detect
anomalous transaction patterns without heavy ML dependencies.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import math
import statistics
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.transaction import Transaction
from app.models.player import Player


# ---------------------------------------------------------------------------
# Z-Score based anomaly detection
# ---------------------------------------------------------------------------

def z_score(value: float, mean: float, std: float) -> float:
    """Compute the z-score of a value given population mean and std."""
    if std == 0:
        return 0.0
    return abs((value - mean) / std)


async def compute_amount_anomaly_score(
    tx_amount: float,
    player_id: str,
    db: AsyncSession,
) -> float:
    """
    Compare current transaction amount against player's historical
    transaction amounts using z-score normalisation.
    Returns a score in [0, 1] where 1 = highly anomalous.
    """
    result = await db.execute(
        select(Transaction.amount)
        .where(
            Transaction.player_id == player_id,
            Transaction.tx_type == "deposit",
        )
        .order_by(Transaction.created_at.desc())
        .limit(100)
    )
    amounts = [row[0] for row in result.fetchall()]

    if len(amounts) < 5:
        # Not enough history — use conservative default
        return 0.1

    mean = statistics.mean(amounts)
    std = statistics.stdev(amounts)
    z = z_score(tx_amount, mean, std)

    # Sigmoid-like normalisation: z=3 → ~0.95
    score = 1 - math.exp(-0.3 * z)
    return min(score, 1.0)


# ---------------------------------------------------------------------------
# Velocity / burst detection
# ---------------------------------------------------------------------------

async def detect_velocity_burst(
    player_id: str,
    window_minutes: int,
    threshold: int,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Detect abnormal burst of transactions in a rolling time window.
    Returns a dict with `is_anomaly`, `count`, and `score`.
    """
    since = datetime.utcnow() - timedelta(minutes=window_minutes)
    result = await db.execute(
        select(func.count(Transaction.id))
        .where(
            Transaction.player_id == player_id,
            Transaction.created_at >= since,
        )
    )
    count = result.scalar() or 0
    is_anomaly = count >= threshold
    score = min(count / max(threshold, 1), 1.0)
    return {"is_anomaly": is_anomaly, "count": count, "score": score}


# ---------------------------------------------------------------------------
# Time-of-day pattern anomaly
# ---------------------------------------------------------------------------

def detect_unusual_hour(created_at: datetime) -> Dict[str, Any]:
    """
    Flag transactions outside normal business hours (00:00–05:00 UTC).
    Returns a dict with `is_anomaly` and `score`.
    """
    hour = created_at.hour
    # Late-night / early-morning window
    is_unusual = 0 <= hour < 5
    score = 0.4 if is_unusual else 0.0
    return {"is_anomaly": is_unusual, "hour": hour, "score": score}


# ---------------------------------------------------------------------------
# Round-number detection (money mule / structuring signal)
# ---------------------------------------------------------------------------

def detect_round_amount(amount: float, threshold: float = 0.01) -> Dict[str, Any]:
    """
    Detect suspiciously round amounts (e.g. 100.00, 500.00, 1000.00).
    These can indicate structuring or automated fraud.
    """
    remainder = amount % 100
    is_round = remainder < threshold or remainder > (100 - threshold)
    score = 0.2 if is_round else 0.0
    return {"is_round": is_round, "amount": amount, "score": score}


# ---------------------------------------------------------------------------
# Composite anomaly score
# ---------------------------------------------------------------------------

async def compute_ml_anomaly_score(
    tx: Transaction,
    player: Player,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Aggregate multiple anomaly signals into a composite ML-style score.
    Returns a dict with detailed signals and a final `composite_score` in [0, 1].
    """
    signals: Dict[str, Any] = {}

    # 1. Amount anomaly
    amount_score = await compute_amount_anomaly_score(tx.amount, tx.player_id, db)
    signals["amount_anomaly"] = {"score": amount_score}

    # 2. Velocity burst (5-minute window)
    velocity = await detect_velocity_burst(tx.player_id, window_minutes=5, threshold=5, db=db)
    signals["velocity_burst"] = velocity

    # 3. Unusual hour
    unusual_hour = detect_unusual_hour(tx.created_at or datetime.utcnow())
    signals["unusual_hour"] = unusual_hour

    # 4. Round amount
    round_amount = detect_round_amount(tx.amount)
    signals["round_amount"] = round_amount

    # 5. New player high-value (no KYC)
    new_player_risk = 0.0
    if not player.kyc_verified and tx.amount > 500:
        new_player_risk = min((tx.amount - 500) / 4500, 0.5)
    signals["new_player_high_value"] = {"score": new_player_risk}

    # Weighted composite
    weights = {
        "amount_anomaly": 0.35,
        "velocity_burst": 0.25,
        "unusual_hour": 0.15,
        "round_amount": 0.10,
        "new_player_high_value": 0.15,
    }

    composite = sum(
        signals[key]["score"] * weight
        for key, weight in weights.items()
    )

    return {
        "composite_score": round(composite, 4),
        "signals": signals,
        "is_anomaly": composite >= 0.5,
        "anomaly_level": (
            "high" if composite >= 0.7
            else "medium" if composite >= 0.4
            else "low"
        ),
    }
