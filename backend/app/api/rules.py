from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.rule import Rule
from app.schemas.rule import RuleOut, RuleCreate, RuleUpdate
from typing import List
import uuid

router = APIRouter(prefix="/rules", tags=["rules"])

@router.get("/", response_model=List[RuleOut])
async def list_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rule).order_by(Rule.priority))
    return result.scalars().all()

@router.post("/", response_model=RuleOut)
async def create_rule(data: RuleCreate, db: AsyncSession = Depends(get_db)):
    rule = Rule(id=str(uuid.uuid4()), **data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule

@router.get("/{rule_id}", response_model=RuleOut)
async def get_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalar()
    if not rule:
        raise HTTPException(404, "Rule not found")
    return rule

@router.put("/{rule_id}", response_model=RuleOut)
async def update_rule(rule_id: str, data: RuleUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalar()
    if not rule:
        raise HTTPException(404, "Rule not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(rule, k, v)
    rule.version = (rule.version or 1) + 1
    await db.commit()
    await db.refresh(rule)
    return rule

@router.delete("/{rule_id}")
async def delete_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalar()
    if rule:
        rule.status = "archived"
        await db.commit()
        return {"ok": True}
    raise HTTPException(404, "Rule not found")

@router.post("/{rule_id}/publish")
async def publish_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalar()
    if not rule:
        raise HTTPException(404, "Rule not found")
    rule.status = "live"
    await db.commit()
    return {"ok": True, "status": "live"}

@router.post("/{rule_id}/test")
async def test_rule(rule_id: str, test_data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalar()
    if not rule:
        raise HTTPException(404, "Rule not found")
    
    # Simple rule evaluation logic
    triggered = False
    reason = ""
    
    if rule.condition_type == "threshold":
        field = rule.condition_field
        operator = rule.condition_operator
        threshold = rule.condition_value
        
        if field in test_data:
            value = test_data[field]
            if operator == "gt" and value > threshold:
                triggered = True
                reason = f"{field} ({value}) > {threshold}"
            elif operator == "lt" and value < threshold:
                triggered = True
                reason = f"{field} ({value}) < {threshold}"
            elif operator == "eq" and value == threshold:
                triggered = True
                reason = f"{field} ({value}) == {threshold}"
    
    return {
        "rule_id": rule_id,
        "rule_name": rule.name,
        "triggered": triggered,
        "reason": reason,
        "action": rule.action if triggered else None,
        "test_data": test_data
    }
