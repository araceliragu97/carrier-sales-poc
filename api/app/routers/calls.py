from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import verify_api_key
from app.database import get_db
from app import models
from app.schemas import CallLogIn, CallLogOut

router = APIRouter(prefix="/calls", tags=["calls"], dependencies=[Depends(verify_api_key)])


@router.post("", response_model=CallLogOut)
def create_call_log(call: CallLogIn, db: Session = Depends(get_db)):
    """
    This is the endpoint the HappyRobot workflow calls (as a Webhook action) right
    after the AI > Classify and AI > Extract steps run at the end of a call.
    Every call gets exactly one row here, regardless of outcome -- an ineligible
    carrier or a failed negotiation is just as important to log as a booked load,
    since the dashboard needs to show the full funnel, not just the wins.

    If the call ended in a booking, this also marks the load as booked so it
    stops appearing in search results for the next carrier.
    """
    db_call = models.CallLog(**call.model_dump())
    db.add(db_call)

    if call.outcome == "booked" and call.load_id:
        load = db.query(models.Load).filter(models.Load.load_id == call.load_id).first()
        if load:
            load.is_booked = 1

    db.commit()
    db.refresh(db_call)
    return db_call


@router.get("", response_model=List[CallLogOut])
def list_call_logs(
    outcome: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Returns raw call records, newest first. The dashboard mostly uses /metrics
    instead, but this is useful for debugging and for a "recent calls" table.
    """
    query = db.query(models.CallLog).order_by(models.CallLog.created_at.desc())
    if outcome:
        query = query.filter(models.CallLog.outcome == outcome)
    return query.limit(limit).all()
