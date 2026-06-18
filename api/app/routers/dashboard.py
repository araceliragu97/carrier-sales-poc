from typing import List

from fastapi import APIRouter
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import Depends

from app.database import get_db
from app import models

# Deliberately separate from /metrics and /calls: those require the operational
# API key (meant for the HappyRobot workflow), while this router is meant to be
# embedded in a public-facing dashboard page. It exposes only aggregated stats
# and a trimmed-down recent-calls view -- no API key required, but also no
# endpoint here can mutate data or return anything we wouldn't want visible to
# anyone with the dashboard link.
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics")
def dashboard_metrics(db: Session = Depends(get_db)):
    """Same aggregation as /metrics, just without requiring the API key."""
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

    # Specifically: how many rounds of back-and-forth does it usually take to
    # actually close a deal? Different question from "average across all calls",
    # since plenty of calls never reach negotiation at all (ineligible carrier,
    # no matching load) and would drag that number down misleadingly.
    avg_offers_booked = (
        db.query(func.avg(models.CallLog.num_offers))
        .filter(models.CallLog.outcome == "booked")
        .scalar()
    )

    avg_call_duration = db.query(func.avg(models.CallLog.call_duration_seconds)).scalar()

    return {
        "total_calls": total_calls,
        "booked_calls": booked_count,
        "conversion_rate": conversion_rate,
        "outcome_breakdown": outcome_counts,
        "sentiment_breakdown": sentiment_counts,
        "avg_loadboard_rate": round(avg_loadboard_rate, 2) if avg_loadboard_rate else None,
        "avg_final_agreed_rate": round(avg_final_rate, 2) if avg_final_rate else None,
        "avg_negotiation_rounds": round(avg_num_offers, 2) if avg_num_offers else 0,
        "avg_negotiation_rounds_booked": round(avg_offers_booked, 2) if avg_offers_booked else 0,
        "avg_call_duration_seconds": round(avg_call_duration, 1) if avg_call_duration else None,
    }


@router.get("/calls")
def dashboard_recent_calls(limit: int = 20, db: Session = Depends(get_db)):
    """
    Trimmed recent-calls feed for the dashboard table. Caps at 20 by default
    and 50 max so the public page can't be used to pull the entire call history.
    """
    limit = min(limit, 50)
    rows = (
        db.query(models.CallLog)
        .order_by(models.CallLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "mc_number": row.mc_number,
            "carrier_name": row.carrier_name,
            "fmcsa_eligible": row.fmcsa_eligible,
            "load_id": row.load_id,
            "loadboard_rate": row.loadboard_rate,
            "final_agreed_rate": row.final_agreed_rate,
            "num_offers": row.num_offers,
            "outcome": row.outcome,
            "sentiment": row.sentiment,
            "call_duration_seconds": row.call_duration_seconds,
            "transcript_summary": row.transcript_summary,
        }
        for row in rows
    ]
