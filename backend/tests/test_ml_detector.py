"""
Unit tests for app.services.ml_detector
Runs with pytest (no database required — pure logic tests).
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ml_detector import (
    z_score,
    detect_unusual_hour,
    detect_round_amount,
    compute_amount_anomaly_score,
    detect_velocity_burst,
    compute_ml_anomaly_score,
)


# ---------------------------------------------------------------------------
# Pure function tests (no I/O)
# ---------------------------------------------------------------------------

class TestZScore:
    def test_zero_std_returns_zero(self):
        assert z_score(100.0, 100.0, 0.0) == 0.0

    def test_no_deviation(self):
        assert z_score(50.0, 50.0, 10.0) == 0.0

    def test_positive_deviation(self):
        result = z_score(80.0, 50.0, 10.0)
        assert result == pytest.approx(3.0)

    def test_always_positive(self):
        # z_score should return absolute value
        assert z_score(20.0, 50.0, 10.0) == pytest.approx(3.0)


class TestDetectUnusualHour:
    def test_early_morning_flagged(self):
        dt = datetime(2024, 1, 1, 3, 0, 0)  # 03:00 UTC
        result = detect_unusual_hour(dt)
        assert result["is_anomaly"] is True
        assert result["score"] > 0

    def test_midnight_flagged(self):
        dt = datetime(2024, 1, 1, 0, 0, 0)
        result = detect_unusual_hour(dt)
        assert result["is_anomaly"] is True

    def test_business_hours_ok(self):
        dt = datetime(2024, 1, 1, 14, 0, 0)  # 14:00 UTC
        result = detect_unusual_hour(dt)
        assert result["is_anomaly"] is False
        assert result["score"] == 0.0

    def test_5am_not_flagged(self):
        dt = datetime(2024, 1, 1, 5, 0, 0)  # boundary
        result = detect_unusual_hour(dt)
        assert result["is_anomaly"] is False


class TestDetectRoundAmount:
    def test_round_hundred(self):
        result = detect_round_amount(100.0)
        assert result["is_round"] is True
        assert result["score"] > 0

    def test_round_five_hundred(self):
        result = detect_round_amount(500.0)
        assert result["is_round"] is True

    def test_non_round_amount(self):
        result = detect_round_amount(137.55)
        assert result["is_round"] is False
        assert result["score"] == 0.0

    def test_near_boundary(self):
        # 99.995 rounds to 100 effectively
        result = detect_round_amount(99.995)
        assert isinstance(result["is_round"], bool)


# ---------------------------------------------------------------------------
# Async tests (mocked database)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestComputeAmountAnomalyScore:
    async def test_insufficient_history_returns_default(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [(100.0,), (200.0,)]  # only 2 records
        mock_db.execute.return_value = mock_result

        score = await compute_amount_anomaly_score(150.0, "player-123", mock_db)
        assert score == pytest.approx(0.1)

    async def test_normal_amount_low_score(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        # Historical amounts around 100
        mock_result.fetchall.return_value = [(r,) for r in [95, 100, 105, 98, 102, 99, 101]]
        mock_db.execute.return_value = mock_result

        score = await compute_amount_anomaly_score(100.0, "player-123", mock_db)
        assert 0.0 <= score <= 0.3

    async def test_extreme_amount_high_score(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        # Tight cluster around 50
        mock_result.fetchall.return_value = [(r,) for r in [48, 50, 52, 49, 51, 50, 50]]
        mock_db.execute.return_value = mock_result

        score = await compute_amount_anomaly_score(5000.0, "player-123", mock_db)
        assert score > 0.8


@pytest.mark.asyncio
class TestDetectVelocityBurst:
    async def test_below_threshold_no_anomaly(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 2
        mock_db.execute.return_value = mock_result

        result = await detect_velocity_burst("player-1", window_minutes=5, threshold=5, db=mock_db)
        assert result["is_anomaly"] is False
        assert result["count"] == 2

    async def test_at_threshold_triggers_anomaly(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db.execute.return_value = mock_result

        result = await detect_velocity_burst("player-1", window_minutes=5, threshold=5, db=mock_db)
        assert result["is_anomaly"] is True

    async def test_score_capped_at_one(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1000
        mock_db.execute.return_value = mock_result

        result = await detect_velocity_burst("player-1", window_minutes=5, threshold=5, db=mock_db)
        assert result["score"] <= 1.0


# ---------------------------------------------------------------------------
# Composite score test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_composite_score_range():
    """Composite score must always be in [0, 1]."""
    # Mock a transaction and player
    mock_tx = MagicMock()
    mock_tx.amount = 250.0
    mock_tx.player_id = "player-abc"
    mock_tx.created_at = datetime(2024, 6, 15, 14, 0, 0)
    mock_tx.tx_type = "deposit"

    mock_player = MagicMock()
    mock_player.kyc_verified = True
    mock_player.pep_flag = False
    mock_player.sanctions_flag = False
    mock_player.bonus_abuse_flag = False
    mock_player.multi_account_flag = False
    mock_player.changebacks = 0

    # Mock the db so both sub-functions return benign values
    mock_db = AsyncMock()
    amounts_result = MagicMock()
    amounts_result.fetchall.return_value = [(r,) for r in [200, 220, 240, 260, 280, 250, 230]]
    count_result = MagicMock()
    count_result.scalar.return_value = 1

    mock_db.execute.side_effect = [amounts_result, count_result]

    result = await compute_ml_anomaly_score(mock_tx, mock_player, mock_db)

    assert 0.0 <= result["composite_score"] <= 1.0
    assert result["anomaly_level"] in ("low", "medium", "high")
    assert isinstance(result["is_anomaly"], bool)
