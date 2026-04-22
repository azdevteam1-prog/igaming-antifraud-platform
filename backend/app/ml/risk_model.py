"""ML-based risk scoring model for fraud detection."""
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta


class RiskScoringModel:
    """Ensemble risk scoring model combining multiple fraud signals."""

    def __init__(self):
        self.weights = {
            'velocity_score': 0.25,
            'amount_anomaly_score': 0.20,
            'behavioral_score': 0.20,
            'geo_risk_score': 0.15,
            'device_risk_score': 0.10,
            'pattern_score': 0.10,
        }
        self.high_risk_countries = ['RU', 'CN', 'NG', 'IN', 'BR']
        self.high_risk_payment_methods = ['cryptocurrency', 'prepaid_card']

    def calculate_risk_score(self, transaction: Dict[str, Any], player_history: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive risk score for a transaction.
        
        Args:
            transaction: Current transaction data
            player_history: Historical player data and patterns
            
        Returns:
            Dict with risk_score (0-100) and breakdown by component
        """
        scores = {
            'velocity_score': self._calculate_velocity_score(transaction, player_history),
            'amount_anomaly_score': self._calculate_amount_anomaly(transaction, player_history),
            'behavioral_score': self._calculate_behavioral_score(transaction, player_history),
            'geo_risk_score': self._calculate_geo_risk(transaction),
            'device_risk_score': self._calculate_device_risk(transaction, player_history),
            'pattern_score': self._calculate_pattern_score(transaction, player_history),
        }
        
        # Weighted ensemble
        risk_score = sum(scores[k] * self.weights[k] for k in scores.keys())
        risk_score = min(100, max(0, risk_score))  # Clamp to [0, 100]
        
        return {
            'risk_score': round(risk_score, 2),
            'risk_level': self._get_risk_level(risk_score),
            'breakdown': scores,
            'flags': self._generate_flags(scores, transaction),
        }

    def _calculate_velocity_score(self, tx: Dict, history: Dict) -> float:
        """Score based on transaction frequency in time windows."""
        deposits_24h = history.get('deposits_24h', 0)
        withdrawals_24h = history.get('withdrawals_24h', 0)
        
        score = 0.0
        if deposits_24h > 5:
            score += min(50, deposits_24h * 5)
        if withdrawals_24h > 3:
            score += min(50, withdrawals_24h * 10)
            
        return min(100, score)

    def _calculate_amount_anomaly(self, tx: Dict, history: Dict) -> float:
        """Detect unusual amounts compared to player baseline."""
        amount = tx.get('amount', 0)
        avg_deposit = history.get('avg_deposit', 100)
        max_deposit = history.get('max_deposit', 1000)
        
        if avg_deposit == 0:
            return 30  # New player, medium risk
        
        ratio = amount / avg_deposit
        
        if ratio > 10:
            return 100
        elif ratio > 5:
            return 70
        elif ratio > 3:
            return 40
        elif ratio < 0.1:
            return 20  # Suspiciously small
        
        return 0

    def _calculate_behavioral_score(self, tx: Dict, history: Dict) -> float:
        """Score based on player behavior patterns."""
        score = 0.0
        player_age_days = history.get('player_age_days', 0)
        
        # New accounts are riskier
        if player_age_days < 1:
            score += 60
        elif player_age_days < 7:
            score += 30
        elif player_age_days < 30:
            score += 15
        
        # Chargeback history
        chargeback_count = history.get('chargeback_count', 0)
        score += min(40, chargeback_count * 20)
        
        # Win/loss ratio anomaly
        win_rate = history.get('win_rate', 0.5)
        if win_rate > 0.9:
            score += 30  # Unusually high win rate
        
        return min(100, score)

    def _calculate_geo_risk(self, tx: Dict) -> float:
        """Geographic risk based on country and IP patterns."""
        score = 0.0
        country = tx.get('country', '')
        
        if country in self.high_risk_countries:
            score += 50
        
        # Check for VPN/proxy indicators
        if tx.get('is_vpn', False) or tx.get('is_proxy', False):
            score += 40
        
        # Country mismatch with account registration
        if tx.get('country_mismatch', False):
            score += 30
        
        return min(100, score)

    def _calculate_device_risk(self, tx: Dict, history: Dict) -> float:
        """Device fingerprinting risk score."""
        score = 0.0
        
        # New device for existing player
        if history.get('is_new_device', False) and history.get('player_age_days', 0) > 30:
            score += 40
        
        # Multiple accounts from same device
        if tx.get('shared_device_count', 0) > 1:
            score += min(60, tx.get('shared_device_count') * 20)
        
        return min(100, score)

    def _calculate_pattern_score(self, tx: Dict, history: Dict) -> float:
        """Detect known fraud patterns."""
        score = 0.0
        
        # Rapid deposit->bet->withdrawal pattern
        if tx.get('type') == 'withdrawal' and history.get('minutes_since_deposit', 999) < 30:
            score += 70
        
        # Round number amounts (often fraud)
        amount = tx.get('amount', 0)
        if amount > 0 and amount % 100 == 0:
            score += 20
        
        # Payment method risk
        if tx.get('payment_method') in self.high_risk_payment_methods:
            score += 30
        
        return min(100, score)

    def _get_risk_level(self, score: float) -> str:
        """Map numeric score to risk level."""
        if score >= 75:
            return 'critical'
        elif score >= 50:
            return 'high'
        elif score >= 25:
            return 'medium'
        return 'low'

    def _generate_flags(self, scores: Dict[str, float], tx: Dict) -> List[str]:
        """Generate human-readable risk flags."""
        flags = []
        
        if scores['velocity_score'] > 60:
            flags.append('high_transaction_velocity')
        if scores['amount_anomaly_score'] > 60:
            flags.append('unusual_amount')
        if scores['geo_risk_score'] > 50:
            flags.append('high_risk_geography')
        if scores['device_risk_score'] > 50:
            flags.append('device_risk')
        if scores['behavioral_score'] > 60:
            flags.append('suspicious_behavior')
        if scores['pattern_score'] > 60:
            flags.append('known_fraud_pattern')
        
        if tx.get('is_vpn'):
            flags.append('vpn_detected')
        if tx.get('shared_device_count', 0) > 2:
            flags.append('multi_accounting_suspected')
        
        return flags


# Singleton instance
risk_model = RiskScoringModel()
