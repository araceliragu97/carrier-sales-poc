from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.database import init_db
from app.routers import loads, carriers, calls, metrics, dashboard

app = FastAPI(
    title="Carrier Sales API",
    description="Backend for the inbound carrier sales agent: load search, "
    "FMCSA verification, and call logging for the metrics dashboard.",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    """No auth required -- used for container/host health checks."""
    return {"status": "ok"}


app.include_router(loads.router)
app.include_router(carriers.router)
app.include_router(calls.router)
app.include_router(metrics.router)
app.include_router(dashboard.router)


@app.get("/", include_in_schema=False)
def serve_dashboard():
    """Serves the static dashboard page -- the deliverable link for Objective 2."""
    return FileResponse(Path(__file__).parent / "static" / "dashboard.html")
