"""
Unit tests for app.services.geo_service
Pure logic tests — no database or network required.
"""

import pytest
from datetime import datetime, timedelta
from app.services.geo_service import (
    get_country_risk_level,
    _haversine_km,
    detect_impossible_travel,
    assess_ip_risk,
    compute_geo_risk_score,
)


# ---------------------------------------------------------------------------
# Country risk level
# ---------------------------------------------------------------------------

class TestGetCountryRiskLevel:
    def test_high_risk_country(self):
        result = get_country_risk_level("RU")
        assert result["level"] == "high"
        assert result["score"] >= 0.8

    def test_restricted_country(self):
        result = get_country_risk_level("US")
        assert result["level"] == "restricted"
        assert result["restricted"] is True
        assert result["score"] == 1.0

    def test_medium_risk_country(self):
        result = get_country_risk_level("NG")
        assert result["level"] == "medium"

    def test_low_risk_country(self):
        result = get_country_risk_level("DE")
        assert result["level"] == "low"
        assert result["score"] < 0.3

    def test_case_insensitive(self):
        lower = get_country_risk_level("ru")
        upper = get_country_risk_level("RU")
        assert lower["level"] == upper["level"]


# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

class TestHaversine:
    def test_same_point_zero_distance(self):
        dist = _haversine_km(51.5, -0.1, 51.5, -0.1)
        assert dist == pytest.approx(0.0, abs=0.01)

    def test_london_to_paris_approx(self):
        # London (51.5, -0.1) to Paris (48.9, 2.3) ≈ 340 km
        dist = _haversine_km(51.5, -0.1, 48.9, 2.3)
        assert 300 < dist < 380

    def test_antipodal_points_max_distance(self):
        # Roughly half Earth circumference
        dist = _haversine_km(0, 0, 0, 180)
        assert dist > 19000


# ---------------------------------------------------------------------------
# Impossible travel
# ---------------------------------------------------------------------------

class TestDetectImpossibleTravel:
    def test_same_location_no_anomaly(self):
        t1 = datetime(2024, 1, 1, 10, 0)
        t2 = datetime(2024, 1, 1, 11, 0)
        result = detect_impossible_travel(51.5, -0.1, t1, 51.5, -0.1, t2)
        assert result["is_impossible"] is False
        assert result["score"] == 0.0

    def test_teleportation_flagged(self):
        # London to Sydney in 1 minute
        t1 = datetime(2024, 1, 1, 10, 0)
        t2 = datetime(2024, 1, 1, 10, 1)
        result = detect_impossible_travel(51.5, -0.1, t1, -33.9, 151.2, t2)
        assert result["is_impossible"] is True
        assert result["score"] > 0.5

    def test_realistic_flight_ok(self):
        # London to New York in 8 hours (~5500 km, ~690 km/h)
        t1 = datetime(2024, 1, 1, 8, 0)
        t2 = datetime(2024, 1, 1, 16, 0)
        result = detect_impossible_travel(51.5, -0.1, t1, 40.7, -74.0, t2)
        # 5500 km / 8h = 687 km/h < 900 km/h threshold
        assert result["is_impossible"] is False


# ---------------------------------------------------------------------------
# IP risk
# ---------------------------------------------------------------------------

class TestAssessIpRisk:
    def test_clean_ip_zero_score(self):
        result = assess_ip_risk()
        assert result["score"] == 0.0
        assert result["flags"] == []
        assert result["is_high_risk"] is False

    def test_tor_flagged(self):
        result = assess_ip_risk(is_tor=True)
        assert "tor" in result["flags"]
        assert result["score"] >= 0.5
        assert result["is_high_risk"] is True

    def test_proxy_and_datacenter(self):
        result = assess_ip_risk(is_proxy=True, is_datacenter=True)
        assert "proxy" in result["flags"]
        assert "datacenter" in result["flags"]

    def test_known_vpn_asn(self):
        result = assess_ip_risk(asn="AS14061")
        assert "known_vpn_asn" in result["flags"]

    def test_score_capped_at_one(self):
        result = assess_ip_risk(is_tor=True, is_proxy=True, is_datacenter=True, asn="AS14061")
        assert result["score"] <= 1.0


# ---------------------------------------------------------------------------
# Composite geo score
# ---------------------------------------------------------------------------

class TestComputeGeoRiskScore:
    def test_low_risk_scenario(self):
        result = compute_geo_risk_score("DE")
        assert result["overall_level"] == "low"
        assert result["composite_score"] < 0.35

    def test_high_risk_country_tor(self):
        result = compute_geo_risk_score("RU", is_tor=True)
        assert result["overall_level"] in ("high", "critical")
        assert result["composite_score"] > 0.5

    def test_restricted_country_always_critical(self):
        result = compute_geo_risk_score("US")
        assert result["overall_level"] == "critical"
        assert result["is_restricted"] is True

    def test_impossible_travel_raises_score(self):
        baseline = compute_geo_risk_score("DE")["composite_score"]
        with_travel = compute_geo_risk_score("DE", impossible_travel_score=1.0)["composite_score"]
        assert with_travel > baseline
