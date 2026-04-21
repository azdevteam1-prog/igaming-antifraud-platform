from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertOut, AlertUpdate
from typing import List, Optional
from datetime import datetime, timezone

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/", response_model=List[AlertOut])
async def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    q = select(Alert).order_by(desc(Alert.created_at)).limit(200)
    if status:
        q = q.where(Alert.status == status)
    if severity:
        q = q.where(Alert.severity == severity)
    result = await db.execute(q)
    return result.scalars().all()

@router.patch("/{alert_id}")
async def update_alert(alert_id: str, data: AlertUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar()
    if alert:
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(alert, k, v)
        if data.status in ["resolved", "false_positive"]:
            alert.resolved_at = datetime.now(timezone.utc)
        await db.commit()
    return {"ok": True}
