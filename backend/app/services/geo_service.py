"""
Geo Risk Service for iGaming Anti-Fraud Platform
Provides country-level risk classification, impossible travel detection,
and VPN/proxy risk signals based on IP and geolocation metadata.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Country risk tiers (based on FATF, EU AML directives, iGaming compliance)
# ---------------------------------------------------------------------------

HIGH_RISK_COUNTRIES = {
    "AF", "BY", "MM", "CF", "CD", "KP", "HT", "IR", "IQ",
    "LY", "ML", "NI", "PK", "PA", "RU", "SO", "SS", "SY",
    "TZ", "UG", "YE", "ZW",
}

MEDIUM_RISK_COUNTRIES = {
    "AL", "BB", "BF", "CM", "GH", "GI", "JM", "MG", "MO",
    "MZ", "NG", "PH", "SN", "TN", "TR", "VG", "VN",
}

RESTRICTED_COUNTRIES = {
    # Jurisdictions typically blocked by iGaming operators
    "US",  # Requires state-level licensing
    "CN",  # Gambling broadly prohibited
    "IN",  # Restricted
    "SG",  # Highly regulated
}


def get_country_risk_level(country_code: str) -> Dict[str, Any]:
    """
    Return risk classification for a given ISO 3166-1 alpha-2 country code.
    """
    code = country_code.upper()
    if code in HIGH_RISK_COUNTRIES:
        return {"level": "high", "score": 0.9, "restricted": False}
    if code in RESTRICTED_COUNTRIES:
        return {"level": "restricted", "score": 1.0, "restricted": True}
    if code in MEDIUM_RISK_COUNTRIES:
        return {"level": "medium", "score": 0.5, "restricted": False}
    return {"level": "low", "score": 0.1, "restricted": False}


# ---------------------------------------------------------------------------
# Impossible travel detection
# ---------------------------------------------------------------------------

# Approximate distances in km between known geographic regions
REGION_COORDS: Dict[str, tuple] = {
    "EU": (54.0, 15.0),
    "NA": (40.0, -100.0),
    "SA": (-15.0, -60.0),
    "AS": (30.0, 100.0),
    "AF": (0.0, 20.0),
    "OC": (-25.0, 135.0),
    "ME": (25.0, 45.0),
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance in kilometres."""
    import math
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def detect_impossible_travel(
    prev_lat: float,
    prev_lon: float,
    prev_time: datetime,
    curr_lat: float,
    curr_lon: float,
    curr_time: datetime,
    max_speed_kmh: float = 900.0,  # approx commercial aircraft speed
) -> Dict[str, Any]:
    """
    Detect physically impossible travel between two login/transaction points.
    Returns a risk signal dict.
    """
    distance_km = _haversine_km(prev_lat, prev_lon, curr_lat, curr_lon)
    time_diff_hours = max((curr_time - prev_time).total_seconds() / 3600, 0.01)
    required_speed = distance_km / time_diff_hours

    is_impossible = required_speed > max_speed_kmh
    score = min(required_speed / (max_speed_kmh * 2), 1.0) if is_impossible else 0.0

    return {
        "is_impossible": is_impossible,
        "distance_km": round(distance_km, 1),
        "time_hours": round(time_diff_hours, 2),
        "required_speed_kmh": round(required_speed, 1),
        "score": round(score, 4),
    }


# ---------------------------------------------------------------------------
# IP risk assessment (VPN / datacenter / Tor signals)
# ---------------------------------------------------------------------------

# Known datacenter / VPN ASN prefixes (illustrative subset)
KNOWN_VPN_ASN_PREFIXES: List[str] = [
    "AS14061",  # DigitalOcean
    "AS16276",  # OVH
    "AS24940",  # Hetzner
    "AS14618",  # Amazon AWS
    "AS15169",  # Google Cloud
    "AS8075",   # Microsoft Azure
    "AS13335",  # Cloudflare
    "AS20473",  # Choopa/Vultr
    "AS9009",   # M247 (VPN provider)
    "AS60068",  # CDN77
]


def assess_ip_risk(
    asn: Optional[str] = None,
    is_tor: bool = False,
    is_proxy: bool = False,
    is_datacenter: bool = False,
) -> Dict[str, Any]:
    """
    Evaluate IP-level risk based on anonymisation signals.
    Returns a risk dict with a score in [0, 1].
    """
    score = 0.0
    flags = []

    if is_tor:
        score += 0.6
        flags.append("tor")

    if is_proxy:
        score += 0.3
        flags.append("proxy")

    if is_datacenter:
        score += 0.2
        flags.append("datacenter")

    if asn and any(asn.upper().startswith(prefix) for prefix in KNOWN_VPN_ASN_PREFIXES):
        score += 0.25
        flags.append("known_vpn_asn")

    score = min(score, 1.0)
    return {
        "score": round(score, 4),
        "flags": flags,
        "is_high_risk": score >= 0.5,
    }


# ---------------------------------------------------------------------------
# Composite geo risk score
# ---------------------------------------------------------------------------

def compute_geo_risk_score(
    country_code: str,
    asn: Optional[str] = None,
    is_tor: bool = False,
    is_proxy: bool = False,
    is_datacenter: bool = False,
    impossible_travel_score: float = 0.0,
) -> Dict[str, Any]:
    """
    Combine country risk, IP risk and travel anomaly into a single geo risk score.
    """
    country_risk = get_country_risk_level(country_code)
    ip_risk = assess_ip_risk(asn, is_tor, is_proxy, is_datacenter)

    weights = {"country": 0.40, "ip": 0.35, "travel": 0.25}
    composite = (
        country_risk["score"] * weights["country"]
        + ip_risk["score"] * weights["ip"]
        + impossible_travel_score * weights["travel"]
    )

    return {
        "composite_score": round(composite, 4),
        "country_risk": country_risk,
        "ip_risk": ip_risk,
        "impossible_travel_score": impossible_travel_score,
        "is_restricted": country_risk["restricted"],
        "overall_level": (
            "critical" if country_risk["restricted"]
            else "high" if composite >= 0.65
            else "medium" if composite >= 0.35
            else "low"
        ),
    }
