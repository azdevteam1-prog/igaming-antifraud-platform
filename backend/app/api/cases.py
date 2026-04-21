import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.security import get_current_user, require_analyst
from app.models.case import Case, CaseComment, CaseStatus, CasePriority, CaseType
from app.models.user import User
from pydantic import BaseModel

router = APIRouter(prefix="/cases", tags=["Cases"])


class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    case_type: CaseType
    priority: CasePriority = CasePriority.medium
    player_id: Optional[str] = None
    tags: Optional[List[str]] = []


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None
    assigned_to: Optional[str] = None
    risk_score: Optional[str] = None
    resolution_notes: Optional[str] = None
    tags: Optional[List[str]] = None


class CommentCreate(BaseModel):
    content: str
    is_internal: bool = True


class CaseResponse(BaseModel):
    id: str
    case_number: str
    title: str
    description: Optional[str]
    case_type: CaseType
    status: CaseStatus
    priority: CasePriority
    player_id: Optional[str]
    risk_score: Optional[str]
    tags: List
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


def generate_case_number() -> str:
    import random
    return f"CASE-{datetime.utcnow().strftime('%Y%m')}-{random.randint(1000, 9999)}"


@router.post("/", response_model=CaseResponse, status_code=201)
def create_case(
    case_data: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    case = Case(
        case_number=generate_case_number(),
        title=case_data.title,
        description=case_data.description,
        case_type=case_data.case_type,
        priority=case_data.priority,
        player_id=case_data.player_id,
        created_by=current_user.id,
        tags=case_data.tags or [],
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("/", response_model=List[CaseResponse])
def list_cases(
    status: Optional[CaseStatus] = None,
    priority: Optional[CasePriority] = None,
    case_type: Optional[CaseType] = None,
    player_id: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    query = db.query(Case)
    if status:
        query = query.filter(Case.status == status)
    if priority:
        query = query.filter(Case.priority == priority)
    if case_type:
        query = query.filter(Case.case_type == case_type)
    if player_id:
        query = query.filter(Case.player_id == player_id)
    if search:
        query = query.filter(
            or_(Case.title.ilike(f"%{search}%"), Case.case_number.ilike(f"%{search}%"))
        )
    return query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_analyst)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: str,
    updates: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    for field, value in updates.dict(exclude_none=True).items():
        setattr(case, field, value)
    if updates.status in [CaseStatus.resolved, CaseStatus.closed]:
        case.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(case)
    return case


@router.post("/{case_id}/comments")
def add_comment(
    case_id: str,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    comment = CaseComment(
        case_id=case.id,
        author_id=current_user.id,
        content=comment_data.content,
        is_internal=str(comment_data.is_internal).lower(),
    )
    db.add(comment)
    db.commit()
    return {"message": "Comment added", "comment_id": str(comment.id)}
