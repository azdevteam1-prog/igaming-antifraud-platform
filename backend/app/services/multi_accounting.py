from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.player import Player
from app.models.transaction import Transaction
from datetime import datetime, timedelta
from typing import List, Dict, Any
import hashlib

class MultiAccountDetector:
    """Service for detecting multi-accounting patterns in iGaming platforms."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def detect_shared_devices(self, player_id: str) -> List[Dict[str, Any]]:
        """Find other players using the same device fingerprint."""
        player_result = await self.db.execute(
            select(Player).where(Player.id == player_id)
        )
        player = player_result.scalar()
        if not player or not player.device_fingerprint:
            return []
        
        # Find players with matching device fingerprint
        result = await self.db.execute(
            select(Player).where(
                and_(
                    Player.device_fingerprint == player.device_fingerprint,
                    Player.id != player_id
                )
            ).limit(50)
        )
        matches = result.scalars().all()
        
        return [{
            "player_id": match.id,
            "username": match.username,
            "email": match.email,
            "device_fingerprint": match.device_fingerprint,
            "risk_score": match.risk_score,
            "created_at": match.created_at.isoformat(),
            "match_type": "device_fingerprint"
        } for match in matches]
    
    async def detect_shared_ip(self, player_id: str) -> List[Dict[str, Any]]:
        """Find other players using the same IP address."""
        player_result = await self.db.execute(
            select(Player).where(Player.id == player_id)
        )
        player = player_result.scalar()
        if not player or not player.ip_address:
            return []
        
        # Find players with matching IP
        result = await self.db.execute(
            select(Player).where(
                and_(
                    Player.ip_address == player.ip_address,
                    Player.id != player_id
                )
            ).limit(50)
        )
        matches = result.scalars().all()
        
        return [{
            "player_id": match.id,
            "username": match.username,
            "ip_address": match.ip_address,
            "risk_score": match.risk_score,
            "created_at": match.created_at.isoformat(),
            "match_type": "ip_address"
        } for match in matches]
    
    async def detect_similar_emails(self, player_id: str) -> List[Dict[str, Any]]:
        """Find accounts with similar email patterns (e.g., john+1@gmail.com, john+2@gmail.com)."""
        player_result = await self.db.execute(
            select(Player).where(Player.id == player_id)
        )
        player = player_result.scalar()
        if not player or not player.email:
            return []
        
        # Extract base email (before + symbol if present)
        email_parts = player.email.split('@')
        if len(email_parts) != 2:
            return []
        
        local_part = email_parts[0].split('+')[0]
        domain = email_parts[1]
        base_pattern = f"{local_part}%@{domain}"
        
        # Find similar emails (simplified - in production use LIKE or regex)
        all_players = await self.db.execute(
            select(Player).where(Player.id != player_id).limit(1000)
        )
        matches = []
        for p in all_players.scalars().all():
            if p.email and p.email.startswith(local_part) and domain in p.email:
                matches.append({
                    "player_id": p.id,
                    "username": p.username,
                    "email": p.email,
                    "risk_score": p.risk_score,
                    "created_at": p.created_at.isoformat(),
                    "match_type": "similar_email"
                })
        
        return matches[:50]
    
    async def detect_behavioral_patterns(self, player_id: str) -> Dict[str, Any]:
        """Analyze transaction patterns to detect multi-accounting."""
        # Get player's transactions
        tx_result = await self.db.execute(
            select(Transaction).where(
                Transaction.player_id == player_id
            ).order_by(Transaction.created_at.desc()).limit(100)
        )
        transactions = tx_result.scalars().all()
        
        if not transactions:
            return {"suspicious_patterns": []}
        
        patterns = []
        
        # Check for rapid account creation followed by large withdrawals
        player_result = await self.db.execute(
            select(Player).where(Player.id == player_id)
        )
        player = player_result.scalar()
        
        if player:
            account_age_days = (datetime.utcnow() - player.created_at).days
            withdrawal_txs = [tx for tx in transactions if tx.tx_type == 'withdrawal']
            
            if account_age_days < 7 and len(withdrawal_txs) > 0:
                total_withdrawal = sum(float(tx.amount) for tx in withdrawal_txs)
                if total_withdrawal > 1000:
                    patterns.append({
                        "type": "rapid_withdrawal",
                        "severity": "high",
                        "description": f"New account ({account_age_days} days) with large withdrawals (${total_withdrawal})"
                    })
        
        return {"suspicious_patterns": patterns}
    
    async def get_full_report(self, player_id: str) -> Dict[str, Any]:
        """Generate comprehensive multi-accounting detection report."""
        device_matches = await self.detect_shared_devices(player_id)
        ip_matches = await self.detect_shared_ip(player_id)
        email_matches = await self.detect_similar_emails(player_id)
        behavioral = await self.detect_behavioral_patterns(player_id)
        
        # Calculate overall risk level
        total_matches = len(device_matches) + len(ip_matches) + len(email_matches)
        risk_level = "low"
        if total_matches > 5:
            risk_level = "high"
        elif total_matches > 2:
            risk_level = "medium"
        
        return {
            "player_id": player_id,
            "risk_level": risk_level,
            "total_matches": total_matches,
            "device_matches": device_matches,
            "ip_matches": ip_matches,
            "email_matches": email_matches,
            "behavioral_analysis": behavioral,
            "generated_at": datetime.utcnow().isoformat()
        }
