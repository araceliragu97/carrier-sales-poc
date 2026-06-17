from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import verify_api_key
from app.database import get_db
from app import models

router = APIRouter(prefix="/metrics", tags=["metrics"], dependencies=[Depends(verify_api_key)])


@router.get("")
def get_metrics(db: Session = Depends(get_db)):
    """
    All the numbers the dashboard needs, computed fresh on every request from
    the call_logs table. For this project's scale (a take-home demo, not millions
    of calls) recomputing on read is simpler and more honest than caching --
    there's no staleness to worry about.
    """
    total_calls = db.query(models.CallLog).count()

    outcome_counts = dict(
        db.query(models.CallLog.outcome, func.count(models.CallLog.id))
        .group_by(models.CallLog.outcome)
        .all()
    )
    sentiment_counts = dict(
        db.query(models.CallLog.sentiment, func.count(models.CallLog.id))
        .group_by(models.CallLog.sentiment)
        .all()
    )

    booked_count = outcome_counts.get("booked", 0)
    conversion_rate = round(booked_count / total_calls, 3) if total_calls else 0.0

    avg_loadboard_rate, avg_final_rate = (
        db.query(
            func.avg(models.CallLog.loadboard_rate),
            func.avg(models.CallLog.final_agreed_rate),
        )
        .filter(models.CallLog.outcome == "booked")
        .first()
    )

    avg_num_offers = db.query(func.avg(models.CallLog.num_offers)).scalar()

    return {
        "total_calls": total_calls,
        "booked_calls": booked_count,
        "conversion_rate": conversion_rate,
        "outcome_breakdown": outcome_counts,
        "sentiment_breakdown": sentiment_counts,
        "avg_loadboard_rate": round(avg_loadboard_rate, 2) if avg_loadboard_rate else None,
        "avg_final_agreed_rate": round(avg_final_rate, 2) if avg_final_rate else None,
        "avg_negotiation_rounds": round(avg_num_offers, 2) if avg_num_offers else 0,
    }
