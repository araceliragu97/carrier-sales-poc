import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# If using SQLite with a nested path (e.g. ./data/carrier_sales.db for the Docker
# volume mount), the parent folder needs to exist before SQLite can create the file.
if settings.DATABASE_URL.startswith("sqlite:///"):
    db_path = Path(settings.DATABASE_URL.replace("sqlite:///", "", 1))
    db_path.parent.mkdir(parents=True, exist_ok=True)

# check_same_thread=False is only needed for SQLite + FastAPI's threaded request handling.
engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

SEED_FILE = Path(__file__).parent / "data" / "loads_seed.json"


def get_db():
    """FastAPI dependency: yields a DB session and always closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Creates tables if they don't exist, and seeds the loads table from the JSON
    file the first time the app runs. Safe to call on every startup.
    """
    from app import models  # local import avoids a circular import with Base

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(models.Load).count() == 0:
            with open(SEED_FILE) as f:
                loads = json.load(f)
            for load in loads:
                db.add(models.Load(**load))
            db.commit()
    finally:
        db.close()
