"""Device Fingerprinting API

Collects and analyzes device fingerprints to detect
multi-accounting, device sharing, and suspicious device patterns.
"""
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.core.security import require_analyst
from app.models.user import User

router = APIRouter(prefix="/fingerprint", tags=["Device Fingerprinting"])


class FingerprintData(BaseModel):
    player_id: str
    user_agent: str
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    platform: Optional[str] = None
    canvas_hash: Optional[str] = None
    webgl_hash: Optional[str] = None
    audio_hash: Optional[str] = None
    fonts: Optional[List[str]] = []
    plugins: Optional[List[str]] = []
    do_not_track: Optional[bool] = None
    cookie_enabled: Optional[bool] = None
    hardware_concurrency: Optional[int] = None
    device_memory: Optional[float] = None
    touch_support: Optional[bool] = None


class FingerprintResponse(BaseModel):
    fingerprint_id: str
    player_id: str
    risk_signals: List[str]
    risk_score: float
    is_known_device: bool
    shared_with_players: List[str]
    created_at: datetime


# In-memory store (replace with Redis/DB in production)
_fingerprint_store: Dict[str, Dict] = {}
_player_devices: Dict[str, List[str]] = {}  # player_id -> [fingerprint_ids]
_device_players: Dict[str, List[str]] = {}  # fingerprint_id -> [player_ids]


def compute_fingerprint_id(data: FingerprintData) -> str:
    """Compute a stable fingerprint hash from device signals."""
    components = [
        data.user_agent,
        data.screen_resolution or "",
        data.timezone or "",
        data.platform or "",
        data.canvas_hash or "",
        data.webgl_hash or "",
        data.audio_hash or "",
        str(data.hardware_concurrency or ""),
        str(data.device_memory or ""),
    ]
    raw = "|".join(components)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def analyze_risk_signals(data: FingerprintData, fp_id: str) -> tuple[List[str], float]:
    """Analyze fingerprint for risk signals."""
    signals = []
    score = 0.0

    # Check if device is shared across multiple players
    existing_players = _device_players.get(fp_id, [])
    if existing_players and data.player_id not in existing_players:
        signals.append(f"DEVICE_SHARED_WITH:{','.join(existing_players)}")
        score += min(len(existing_players) * 25, 75)

    # Check automation signals
    if data.user_agent and any(
        bot in data.user_agent.lower()
        for bot in ["selenium", "puppeteer", "playwright", "headless", "phantomjs"]
    ):
        signals.append("AUTOMATION_DETECTED")
        score += 40

    # Missing canvas/webgl hashes suggest privacy mode or spoofing
    if not data.canvas_hash and not data.webgl_hash:
        signals.append("CANVAS_WEBGL_BLOCKED")
        score += 10

    # VPN/proxy detection via timezone mismatch (placeholder)
    if data.timezone and data.timezone in ["UTC", "GMT"]:
        signals.append("POSSIBLE_VPN_TIMEZONE")
        score += 5

    # No plugins may indicate headless browser
    if not data.plugins:
        signals.append("NO_BROWSER_PLUGINS")
        score += 5

    return signals, min(round(score, 2), 100.0)


@router.post("/collect", response_model=FingerprintResponse)
def collect_fingerprint(
    request: Request,
    fp_data: FingerprintData,
    current_user: User = Depends(require_analyst),
):
    """Collect and analyze a device fingerprint."""
    fp_id = compute_fingerprint_id(fp_data)
    risk_signals, risk_score = analyze_risk_signals(fp_data, fp_id)

    is_known = fp_id in _fingerprint_store
    shared_with = [
        p for p in _device_players.get(fp_id, []) if p != fp_data.player_id
    ]

    # Store fingerprint
    _fingerprint_store[fp_id] = {
        "player_id": fp_data.player_id,
        "user_agent": fp_data.user_agent,
        "risk_signals": risk_signals,
        "risk_score": risk_score,
        "ip": request.client.host if request.client else "unknown",
        "created_at": datetime.utcnow().isoformat(),
    }

    # Update player-device mappings
    if fp_id not in _device_players:
        _device_players[fp_id] = []
    if fp_data.player_id not in _device_players[fp_id]:
        _device_players[fp_id].append(fp_data.player_id)

    if fp_data.player_id not in _player_devices:
        _player_devices[fp_data.player_id] = []
    if fp_id not in _player_devices[fp_data.player_id]:
        _player_devices[fp_data.player_id].append(fp_id)

    return FingerprintResponse(
        fingerprint_id=fp_id,
        player_id=fp_data.player_id,
        risk_signals=risk_signals,
        risk_score=risk_score,
        is_known_device=is_known,
        shared_with_players=shared_with,
        created_at=datetime.utcnow(),
    )


@router.get("/player/{player_id}")
def get_player_devices(
    player_id: str,
    current_user: User = Depends(require_analyst),
):
    """Get all device fingerprints for a player."""
    device_ids = _player_devices.get(player_id, [])
    devices = []
    for fp_id in device_ids:
        fp = _fingerprint_store.get(fp_id, {})
        devices.append({"fingerprint_id": fp_id, **fp})
    return {"player_id": player_id, "total_devices": len(devices), "devices": devices}


@router.get("/device/{fingerprint_id}/players")
def get_device_players(
    fingerprint_id: str,
    current_user: User = Depends(require_analyst),
):
    """Get all players using a specific device fingerprint."""
    players = _device_players.get(fingerprint_id, [])
    is_shared = len(players) > 1
    return {
        "fingerprint_id": fingerprint_id,
        "players": players,
        "is_shared_device": is_shared,
        "multi_account_risk": is_shared,
    }
