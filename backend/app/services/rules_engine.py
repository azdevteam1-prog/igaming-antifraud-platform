from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.rule import Rule
from app.models.transaction import Transaction
from app.models.player import Player
from datetime import datetime, timedelta

DEFAULT_RULES = [
    {
        "code": "DEP_VELOCITY_10M",
        "name": "Deposit Velocity 10 min",
        "description": "3+ deposits in 10 minutes from same player",
        "category": "velocity",
        "condition_type": "threshold",
        "condition_params": {"field": "deposit_count", "operator": "gte", "value": 3, "window_seconds": 600},
        "risk_points": 25,
        "action": "review",
        "status": "live",
        "priority": 2,
    },
    {
        "code": "WDR_FAST_CASHOUT",
        "name": "Fast Cashout",
        "description": "Withdrawal within 15 min after deposit",
        "category": "behavior",
        "condition_type": "threshold",
        "condition_params": {"field": "time_since_last_deposit", "operator": "lte", "value": 900, "window_seconds": 900},
        "risk_points": 35,
        "action": "hold",
        "status": "live",
        "priority": 1,
    },
    {
        "code": "IP_SHARED",
        "name": "Shared IP Multi-Account",
        "description": "Same IP used by 3+ accounts in 24h",
        "category": "device",
        "condition_type": "threshold",
        "condition_params": {"field": "ip_account_count", "operator": "gte", "value": 3, "window_seconds": 86400},
        "risk_points": 40,
        "action": "alert",
        "status": "live",
        "priority": 1,
    },
    {
        "code": "GEO_MISMATCH",
        "name": "Geo Mismatch",
        "description": "Transaction country differs from registration",
        "category": "geo",
        "condition_type": "match",
        "condition_params": {"field": "geo_mismatch_flag", "operator": "eq", "value": True},
        "risk_points": 15,
        "action": "review",
        "status": "live",
        "priority": 3,
    },
    {
        "code": "HIGH_RISK_COUNTRY",
        "name": "High Risk Country",
        "description": "Player or IP from high-risk jurisdiction",
        "category": "geo",
        "condition_type": "match",
        "condition_params": {"field": "country", "operator": "in", "value": ["CY", "UA", "RU", "IR", "KP"]},
        "risk_points": 20,
        "action": "review",
        "status": "live",
        "priority": 2,
    },
    {
        "code": "LARGE_WITHDRAWAL",
        "name": "Large Withdrawal",
        "description": "Single withdrawal over 3000 EUR",
        "category": "aml",
        "condition_type": "threshold",
        "condition_params": {"field": "amount", "operator": "gte", "value": 3000, "window_seconds": 0},
        "risk_points": 20,
        "action": "review",
        "status": "live",
        "priority": 2,
    },
    {
        "code": "NO_KYC_WITHDRAWAL",
        "name": "No KYC Withdrawal",
        "description": "Withdrawal attempted without KYC verification",
        "category": "aml",
        "condition_type": "match",
        "condition_params": {"field": "kyc_verified", "operator": "eq", "value": False},
        "risk_points": 30,
        "action": "block",
        "status": "live",
        "priority": 1,
    },
    {
        "code": "BONUS_ABUSE",
        "name": "Bonus Abuse Pattern",
        "description": "Player flagged for bonus abuse",
        "category": "behavior",
        "condition_type": "match",
        "condition_params": {"field": "bonus_abuse_flag", "operator": "eq", "value": True},
        "risk_points": 25,
        "action": "review",
        "status": "live",
        "priority": 2,
    },
]

async def seed_rules():
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Rule).limit(1))
        if result.scalar():
            return
        for r in DEFAULT_RULES:
            rule = Rule(**r)
            db.add(rule)
        await db.commit()

async def evaluate_rules(tx: Transaction, player: Player, db: AsyncSession) -> list:
    result = await db.execute(select(Rule).where(Rule.status == "live").order_by(Rule.priority))
    rules = result.scalars().all()
    hits = []
    for rule in rules:
        p = rule.condition_params
        field = p.get("field")
        op = p.get("operator")
        val = p.get("value")
        triggered = False

        if field == "geo_mismatch_flag":
            triggered = tx.geo_mismatch_flag == val
        elif field == "country":
            triggered = tx.country in val if op == "in" else False
        elif field == "amount" and op == "gte":
            triggered = tx.amount >= val and tx.tx_type == "withdrawal"
        elif field == "kyc_verified" and op == "eq":
            triggered = (not player.kyc_verified) and tx.tx_type == "withdrawal"
        elif field == "bonus_abuse_flag":
            triggered = player.bonus_abuse_flag == val
        elif field == "ip_account_count":
            # simplified: flag if player has multi_account_flag
            triggered = player.multi_account_flag
        elif field == "deposit_count":
            # check recent deposits count
            from datetime import timezone
            window = timedelta(seconds=p.get("window_seconds", 600))
            cutoff = datetime.now(timezone.utc) - window
            count_result = await db.execute(
                select(func.count()).select_from(Transaction).where(
                    Transaction.player_id == player.id,
                    Transaction.tx_type == "deposit",
                    Transaction.created_at >= cutoff
                )
            )
            count = count_result.scalar() or 0
            triggered = count >= val

        if triggered:
            hits.append({
                "rule_code": rule.code,
                "rule_name": rule.name,
                "risk_points": rule.risk_points,
                "action": rule.action,
            })
            rule.hit_count = (rule.hit_count or 0) + 1

    await db.commit()
    return hits
