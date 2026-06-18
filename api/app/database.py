import json
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
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


def _ensure_columns_exist(model):
    """
    Tiny home-grown migration. SQLAlchemy's create_all() only creates tables
    that don't exist yet -- it never alters an existing table to add a column
    a model gained later. For a project this size, a full migration tool like
    Alembic would be overkill, so this just diffs the live table against the
    model and adds whatever's missing with a plain ALTER TABLE. Safe to run on
    every startup: it's a no-op once the columns already match.
    """
    inspector = inspect(engine)
    if model.__tablename__ not in inspector.get_table_names():
        return  # table doesn't exist yet -- create_all() will have just made it fresh

    existing = {col["name"] for col in inspector.get_columns(model.__tablename__)}
    with engine.connect() as conn:
        for column in model.__table__.columns:
            if column.name in existing:
                continue
            col_type = column.type.compile(engine.dialect)
            conn.execute(text(f"ALTER TABLE {model.__tablename__} ADD COLUMN {column.name} {col_type}"))
            conn.commit()


def init_db():
    """
    Creates tables if they don't exist, adds any columns models have gained
    since the table was created, and seeds the loads table from the JSON file
    the first time the app runs. Safe to call on every startup.
    """
    from app import models  # local import avoids a circular import with Base

    Base.metadata.create_all(bind=engine)
    _ensure_columns_exist(models.CallLog)
    _ensure_columns_exist(models.Load)

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
