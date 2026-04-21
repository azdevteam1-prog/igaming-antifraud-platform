"""Player Behavioral Profile Service

Builds and maintains behavioral profiles for players.
Detects anomalies, velocity spikes, and multi-accounting signals.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import hashlib
import json


@dataclass
class BehaviorMetrics:
    """Core behavioral metrics for a player."""
    player_id: str
    avg_session_duration: float = 0.0  # minutes
    avg_deposit_amount: float = 0.0
    avg_withdrawal_amount: float = 0.0
    total_sessions_30d: int = 0
    total_deposits_30d: int = 0
    total_withdrawals_30d: int = 0
    unique_devices: int = 0
    unique_ips: int = 0
    countries: List[str] = field(default_factory=list)
    preferred_games: List[str] = field(default_factory=list)
    activity_hours: Dict[int, int] = field(default_factory=dict)  # hour -> count
    deposit_velocity_score: float = 0.0
    withdrawal_velocity_score: float = 0.0
    device_switch_score: float = 0.0
    geo_anomaly_score: float = 0.0
    overall_risk_score: float = 0.0
    risk_flags: List[str] = field(default_factory=list)
    last_updated: Optional[datetime] = None


class PlayerProfiler:
    """Builds behavioral profiles and detects anomalies."""

    RISK_THRESHOLDS = {
        "high_velocity_deposits": 5,     # deposits per hour
        "rapid_withdrawal": 3,            # withdrawals within 1 hour
        "device_switches": 5,             # unique devices in 30 days
        "ip_switches": 10,                # unique IPs in 30 days
        "multi_country": 3,               # different countries in 7 days
        "night_activity_ratio": 0.8,      # >80% activity between 00:00-06:00
    }

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._cache: Dict[str, BehaviorMetrics] = {}

    def build_profile(self, player_id: str, events: List[Dict]) -> BehaviorMetrics:
        """Build a behavioral profile from a list of player events."""
        profile = BehaviorMetrics(player_id=player_id)
        deposits = [e for e in events if e.get("type") == "deposit"]
        withdrawals = [e for e in events if e.get("type") == "withdrawal"]
        sessions = [e for e in events if e.get("type") == "session"]

        if deposits:
            profile.avg_deposit_amount = sum(e.get("amount", 0) for e in deposits) / len(deposits)
            profile.total_deposits_30d = len(deposits)

        if withdrawals:
            profile.avg_withdrawal_amount = sum(e.get("amount", 0) for e in withdrawals) / len(withdrawals)
            profile.total_withdrawals_30d = len(withdrawals)

        if sessions:
            durations = [e.get("duration_minutes", 0) for e in sessions]
            profile.avg_session_duration = sum(durations) / len(durations)
            profile.total_sessions_30d = len(sessions)

        unique_devices = set(e.get("device_id") for e in events if e.get("device_id"))
        unique_ips = set(e.get("ip_address") for e in events if e.get("ip_address"))
        profile.unique_devices = len(unique_devices)
        profile.unique_ips = len(unique_ips)

        countries = list(set(e.get("country") for e in events if e.get("country")))
        profile.countries = countries

        activity_hours: Dict[int, int] = {}
        for event in events:
            ts = event.get("timestamp")
            if ts:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                hour = ts.hour
                activity_hours[hour] = activity_hours.get(hour, 0) + 1
        profile.activity_hours = activity_hours

        profile.risk_flags = self._detect_risk_flags(profile, events)
        profile.overall_risk_score = self._calculate_risk_score(profile)
        profile.last_updated = datetime.utcnow()

        self._cache[player_id] = profile
        return profile

    def _detect_risk_flags(self, profile: BehaviorMetrics, events: List[Dict]) -> List[str]:
        flags = []
        t = self.RISK_THRESHOLDS

        if profile.unique_devices > t["device_switches"]:
            flags.append(f"HIGH_DEVICE_SWITCHES:{profile.unique_devices}")

        if profile.unique_ips > t["ip_switches"]:
            flags.append(f"HIGH_IP_SWITCHES:{profile.unique_ips}")

        if len(profile.countries) >= t["multi_country"]:
            flags.append(f"MULTI_COUNTRY:{','.join(profile.countries)}")

        # Night activity detection
        night_hours = {0, 1, 2, 3, 4, 5}
        total_events = sum(profile.activity_hours.values()) or 1
        night_events = sum(v for k, v in profile.activity_hours.items() if k in night_hours)
        if night_events / total_events > t["night_activity_ratio"]:
            flags.append("UNUSUAL_NIGHT_ACTIVITY")

        # Rapid withdrawal detection
        withdrawals = [e for e in events if e.get("type") == "withdrawal"]
        if len(withdrawals) >= t["rapid_withdrawal"]:
            flags.append("RAPID_WITHDRAWALS")

        # Deposit-then-withdraw pattern
        if profile.total_deposits_30d > 0 and profile.avg_withdrawal_amount > profile.avg_deposit_amount * 1.5:
            flags.append("WITHDRAW_EXCEEDS_DEPOSIT_PATTERN")

        return flags

    def _calculate_risk_score(self, profile: BehaviorMetrics) -> float:
        """Calculate overall risk score 0-100."""
        score = 0.0
        score += min(profile.unique_devices * 5, 25)
        score += min(profile.unique_ips * 2, 20)
        score += min(len(profile.countries) * 5, 20)
        score += len(profile.risk_flags) * 5
        return min(round(score, 2), 100.0)

    def get_profile(self, player_id: str) -> Optional[BehaviorMetrics]:
        """Retrieve cached profile."""
        return self._cache.get(player_id)

    def compare_players(self, player_a: str, player_b: str) -> Dict[str, Any]:
        """Compare two player profiles to detect shared identity signals."""
        profile_a = self._cache.get(player_a)
        profile_b = self._cache.get(player_b)
        if not profile_a or not profile_b:
            return {"error": "One or both profiles not found"}
        shared_countries = set(profile_a.countries) & set(profile_b.countries)
        similarity_score = len(shared_countries) * 10
        return {
            "player_a": player_a,
            "player_b": player_b,
            "shared_countries": list(shared_countries),
            "similarity_score": min(similarity_score, 100),
            "multi_account_risk": similarity_score > 30,
        }


# Singleton instance
profiler = PlayerProfiler()
