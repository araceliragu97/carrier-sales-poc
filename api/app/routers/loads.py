from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import verify_api_key
from app.database import get_db
from app import models
from app.schemas import LoadOut

router = APIRouter(prefix="/loads", tags=["loads"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=List[LoadOut])
def search_loads(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    equipment_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Searches available (not yet booked) loads. All filters are optional and
    case-insensitive partial matches, since a carrier on a call will say things
    like "Dallas" rather than "Dallas, TX" -- exact matching would fail constantly.

    This is the endpoint the HappyRobot agent calls right after it gets the
    carrier's MC number, using whatever lane/equipment info the carrier mentions.
    """
    query = db.query(models.Load).filter(models.Load.is_booked == 0)

    if origin:
        query = query.filter(models.Load.origin.ilike(f"%{origin}%"))
    if destination:
        query = query.filter(models.Load.destination.ilike(f"%{destination}%"))
    if equipment_type:
        query = query.filter(models.Load.equipment_type.ilike(f"%{equipment_type}%"))

    results = query.limit(5).all()
    return results


@router.get("/{load_id}", response_model=LoadOut)
def get_load(load_id: str, db: Session = Depends(get_db)):
    load = db.query(models.Load).filter(models.Load.load_id == load_id).first()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    return load


@router.post("/{load_id}/book")
def book_load(load_id: str, db: Session = Depends(get_db)):
    """
    Marks a load as booked once a price is agreed, so it stops showing up in
    search results for the next carrier who calls in.
    """
    load = db.query(models.Load).filter(models.Load.load_id == load_id).first()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    load.is_booked = 1
    db.commit()
    return {"load_id": load_id, "is_booked": True}
