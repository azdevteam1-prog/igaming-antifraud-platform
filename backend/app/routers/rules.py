from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..schemas.rule import (
    RuleCreate,
    RuleUpdate,
    RuleResponse,
    RuleExecutionResult
)
from ..models import Rule
from ..core.security import get_current_user

router = APIRouter(
    prefix="/rules",
    tags=["rules"]
)


@router.post("/", response_model=RuleResponse)
async def create_rule(
    rule: RuleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new fraud detection rule."""
    
    # Check if rule with same name exists
    existing = db.query(Rule).filter(Rule.name == rule.name).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Rule with name '{rule.name}' already exists"
        )
    
    db_rule = Rule(
        **rule.dict(),
        created_by=current_user.get('user_id'),
        updated_by=current_user.get('user_id')
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    return db_rule


@router.get("/", response_model=List[RuleResponse])
async def get_rules(
    active_only: bool = Query(False),
    rule_type: Optional[str] = None,
    min_severity: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all fraud detection rules."""
    
    query = db.query(Rule)
    
    if active_only:
        query = query.filter(Rule.is_active == True)
    if rule_type:
        query = query.filter(Rule.rule_type == rule_type)
    if min_severity:
        severity_order = ['low', 'medium', 'high', 'critical']
        if min_severity in severity_order:
            min_index = severity_order.index(min_severity)
            allowed_severities = severity_order[min_index:]
            query = query.filter(Rule.severity.in_(allowed_severities))
    
    rules = query.offset(skip).limit(limit).all()
    return rules


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific rule by ID."""
    
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return rule


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: str,
    rule_update: RuleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an existing fraud detection rule."""
    
    db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Update fields
    update_data = rule_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_rule, field, value)
    
    db_rule.updated_by = current_user.get('user_id')
    db_rule.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_rule)
    
    return db_rule


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a fraud detection rule."""
    
    db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db.delete(db_rule)
    db.commit()
    
    return {"message": f"Rule {rule_id} deleted successfully"}


@router.post("/{rule_id}/activate")
async def activate_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Activate a fraud detection rule."""
    
    db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db_rule.is_active = True
    db_rule.updated_by = current_user.get('user_id')
    db_rule.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Rule {rule_id} activated", "is_active": True}


@router.post("/{rule_id}/deactivate")
async def deactivate_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Deactivate a fraud detection rule."""
    
    db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db_rule.is_active = False
    db_rule.updated_by = current_user.get('user_id')
    db_rule.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Rule {rule_id} deactivated", "is_active": False}


@router.get("/{rule_id}/stats")
async def get_rule_stats(
    rule_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get statistics for a specific rule."""
    
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # In a real implementation, you would query alert/detection history
    # For now, return basic stats
    return {
        'rule_id': rule_id,
        'rule_name': rule.name,
        'period_days': days,
        'total_triggers': 0,  # Would be calculated from alert history
        'true_positives': 0,
        'false_positives': 0,
        'accuracy': 0.0
    }
