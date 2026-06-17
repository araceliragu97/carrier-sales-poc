from sqlalchemy import Column, Float, Integer, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Load(Base):
    """One row per load. Matches the field list from the challenge spec exactly."""

    __tablename__ = "loads"

    load_id = Column(String, primary_key=True, index=True)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    pickup_datetime = Column(String, nullable=False)
    delivery_datetime = Column(String, nullable=False)
    equipment_type = Column(String, nullable=False, index=True)
    loadboard_rate = Column(Float, nullable=False)
    notes = Column(String, nullable=True)
    weight = Column(Integer, nullable=True)
    commodity_type = Column(String, nullable=True)
    num_of_pieces = Column(Integer, nullable=True)
    miles = Column(Integer, nullable=True)
    dimensions = Column(String, nullable=True)
    # Once a load is booked we don't want the agent to keep offering it to other carriers.
    is_booked = Column(Integer, default=0)  # 0/1 used instead of Boolean for SQLite simplicity


class CallLog(Base):
    """
    One row per completed carrier call. This table is the entire data source for
    the metrics dashboard -- intentionally separate from anything HappyRobot stores,
    since the challenge asks for a self-built reporting mechanism.
    """

    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, server_default=func.now())

    mc_number = Column(String, nullable=True)
    carrier_name = Column(String, nullable=True)
    fmcsa_eligible = Column(Integer, nullable=True)  # 0/1/None (None = lookup never happened)

    load_id = Column(String, nullable=True)
    loadboard_rate = Column(Float, nullable=True)
    final_agreed_rate = Column(Float, nullable=True)
    num_offers = Column(Integer, default=0)  # how many negotiation rounds happened

    outcome = Column(String, nullable=True)     # e.g. booked, negotiation_failed, ineligible_carrier, no_matching_load
    sentiment = Column(String, nullable=True)    # e.g. positive, neutral, negative

    transcript_summary = Column(String, nullable=True)
