from app.models.transaction import Transaction
from app.models.player import Player

async def compute_risk_score(tx: Transaction, player: Player, rule_hits: list) -> tuple:
    # Base score from rule hits
    rule_score = sum(h["risk_points"] for h in rule_hits)

    # Normalize to 0-1
    normalized_rule = min(rule_score / 100.0, 1.0)

    # Player history signals
    history_score = 0.0
    if player.pep_flag:
        history_score += 0.2
    if player.sanctions_flag:
        history_score += 0.4
    if player.bonus_abuse_flag:
        history_score += 0.15
    if player.multi_account_flag:
        history_score += 0.2
    if player.chargebacks and player.chargebacks > 0:
        history_score += min(player.chargebacks * 0.05, 0.2)
    if not player.kyc_verified and tx.tx_type == "withdrawal":
        history_score += 0.15

    # Transaction signals
    tx_score = 0.0
    if tx.amount > 3000:
        tx_score += 0.15
    if tx.amount > 8000:
        tx_score += 0.15
    if tx.geo_mismatch_flag:
        tx_score += 0.1
    if tx.payment_method in ["crypto", "prepaid"]:
        tx_score += 0.05

    # Weighted final score
    final_score = (
        0.50 * normalized_rule +
        0.30 * min(history_score, 1.0) +
        0.20 * min(tx_score, 1.0)
    )
    final_score = round(min(final_score, 1.0), 3)

    if final_score >= 0.75:
        label = "Critical"
    elif final_score >= 0.50:
        label = "High"
    elif final_score >= 0.25:
        label = "Medium"
    else:
        label = "Low"

    return final_score, label
