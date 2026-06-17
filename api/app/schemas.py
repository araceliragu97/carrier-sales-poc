from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LoadOut(BaseModel):
    load_id: str
    origin: str
    destination: str
    pickup_datetime: str
    delivery_datetime: str
    equipment_type: str
    loadboard_rate: float
    notes: Optional[str] = None
    weight: Optional[int] = None
    commodity_type: Optional[str] = None
    num_of_pieces: Optional[int] = None
    miles: Optional[int] = None
    dimensions: Optional[str] = None

    class Config:
        from_attributes = True  # lets us build this directly from a SQLAlchemy row


class CarrierVerifyRequest(BaseModel):
    mc_number: str


class CarrierVerifyResponse(BaseModel):
    mc_number: str
    eligible: bool
    carrier_name: Optional[str] = None
    reason: Optional[str] = None  # human-readable explanation, useful for the agent to relay


class CallLogIn(BaseModel):
    """
    What the HappyRobot workflow POSTs after a call ends. Every field is optional
    because not every call reaches every stage (e.g. an ineligible carrier never
    gets to the negotiation step).
    """

    mc_number: Optional[str] = None
    carrier_name: Optional[str] = None
    fmcsa_eligible: Optional[bool] = None
    load_id: Optional[str] = None
    loadboard_rate: Optional[float] = None
    final_agreed_rate: Optional[float] = None
    num_offers: Optional[int] = 0
    outcome: str  # required -- every call must be classified
    sentiment: Optional[str] = None
    transcript_summary: Optional[str] = None


class CallLogOut(CallLogIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
