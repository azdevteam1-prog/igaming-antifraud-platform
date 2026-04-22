from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.multi_accounting import MultiAccountDetector
from typing import List

router = APIRouter(prefix="/multi-accounting", tags=["multi-accounting"])

@router.get("/detect/{player_id}")
async def detect_multi_accounting(
    player_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Run comprehensive multi-accounting detection for a player."""
    detector = MultiAccountDetector(db)
    report = await detector.get_full_report(player_id)
    return report

@router.get("/device-matches/{player_id}")
async def get_device_matches(
    player_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Find players sharing the same device fingerprint."""
    detector = MultiAccountDetector(db)
    matches = await detector.detect_shared_devices(player_id)
    return {"player_id": player_id, "matches": matches, "count": len(matches)}

@router.get("/ip-matches/{player_id}")
async def get_ip_matches(
    player_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Find players sharing the same IP address."""
    detector = MultiAccountDetector(db)
    matches = await detector.detect_shared_ip(player_id)
    return {"player_id": player_id, "matches": matches, "count": len(matches)}

@router.get("/email-matches/{player_id}")
async def get_email_matches(
    player_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Find accounts with similar email patterns."""
    detector = MultiAccountDetector(db)
    matches = await detector.detect_similar_emails(player_id)
    return {"player_id": player_id, "matches": matches, "count": len(matches)}

@router.get("/behavioral-analysis/{player_id}")
async def get_behavioral_analysis(
    player_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Analyze player behavior for multi-accounting patterns."""
    detector = MultiAccountDetector(db)
    analysis = await detector.detect_behavioral_patterns(player_id)
    return {"player_id": player_id, "analysis": analysis}

@router.get("/bulk-scan")
async def bulk_scan_players(
    limit: int = Query(100, le=500),
    min_risk_score: int = Query(50, ge=0, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Scan multiple high-risk players for multi-accounting."""
    # This would be implemented with background jobs in production
    # For now, return a placeholder response
    return {
        "status": "scan_initiated",
        "message": f"Scanning top {limit} players with risk_score >= {min_risk_score}",
        "note": "In production, this would trigger background jobs for each player"
    }
