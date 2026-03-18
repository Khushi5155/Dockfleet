import subprocess
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Query, Request
from fastapi.responses import (
    HTMLResponse,
    StreamingResponse,
)
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from dockfleet.dashboard.services import get_services
from dockfleet.core.logs import stream_container_logs
from dockfleet.health.status import (
    record_manual_restart_event,
    record_manual_stop,
)
from dockfleet.health.logs import (
    query_logs,
    iter_logs_as_text,
    iter_logs_as_csv,
)

router = APIRouter()

templates = Jinja2Templates(directory="dockfleet/dashboard/templates")


# ------------------------------------------------
# Basic health endpoint
# ------------------------------------------------
@router.get("/health")
def health_check():
    return {"status": "ok"}


# ------------------------------------------------
# Service schema (for documentation / typing)
# ------------------------------------------------
class Service(BaseModel):
    name: str
    status: str
    health_status: str
    image: str
    ports: str | None
    restart_policy: str
    restart_count: int
    last_health_check: Optional[datetime] = None

    cpu: Optional[str] = None
    memory: Optional[str] = None
    uptime: Optional[str] = None
    cpu_limit: Optional[str] = None
    memory_limit: Optional[str] = None


class ActionResponse(BaseModel):
    ok: bool
    message: str


# ------------------------------------------------
# Dashboard homepage
# ------------------------------------------------
@router.get("/", response_class=HTMLResponse)
def dashboard_home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


# ------------------------------------------------
# List services
# Combines DB state + Docker runtime stats
# ------------------------------------------------
@router.get("/services", response_model=List[Service])
def list_services():
    return get_services()


# ------------------------------------------------
# Restart service
# ------------------------------------------------
@router.post("/services/{name}/restart", response_model=ActionResponse)
def restart_service(name: str):
    container = f"dockfleet_{name}"

    result = subprocess.run(
        ["docker", "restart", container],
        capture_output=True,
    )

    ok = result.returncode == 0

    if ok:
        # Update DB restart_count + insert RestartEvent
        record_manual_restart_event(name)

    return {
        "message": f"{name} restarted",
        "ok": ok,
    }


# ------------------------------------------------
# Stop service
# ------------------------------------------------
@router.post("/services/{name}/stop", response_model=ActionResponse)
def stop_service(name: str):
    container = f"dockfleet_{name}"

    result = subprocess.run(
        ["docker", "stop", container],
        capture_output=True,
    )

    ok = result.returncode == 0

    if ok:
        # Update DB status -> stopped
        record_manual_stop(name)

    return {
        "message": f"{name} stopped",
        "ok": ok,
    }


# ------------------------------------------------
# DB-backed logs metadata API (for viewer + infinite scroll)
# ------------------------------------------------
@router.get("/logs/db")
def list_logs(
    service_name: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    Return recent log events from DB.

    - Optional filtering by service name and search text.
    - limit/offset for pagination (dashboard infinite scroll).
    """
    events = query_logs(
        service_name=service_name,
        q=q,
        limit=limit,
        offset=offset,
    )

    return [
        {
            "id": log.id,
            "service_name": log.service_name,
            "timestamp": log.created_at,
            "level": log.level,
            "message": log.message,
            "source": log.source,
        }
        for log in events
    ]


# ------------------------------------------------
# Legacy /logs: live docker logs for a service (non-DB)
# ------------------------------------------------
@router.get("/logs")
def get_logs(
    service_name: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = Query(100),
):
    """
    Live docker logs for a service (non-persisted), with optional
    substring filter, used by CLI / live views.
    """
    from dockfleet.core.logs import get_logs_for_service

    # Prevent crash when no service selected
    if not service_name:
        return []

    logs = get_logs_for_service(service_name, limit)

    # Search filter in-memory
    if q:
        logs = [log for log in logs if q.lower() in log.lower()]

    return logs


# ------------------------------------------------
# Download logs from DB (streaming)
# ------------------------------------------------
@router.get("/logs/download")
def download_logs(
    service_name: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    format: str = Query("text", pattern="^(text|csv)$"),
):
    """
    Download logs stored in DB.

    - Uses same filters as /logs/db (service_name, q).
    - format=text: plain text lines, good for quick view.
    - format=csv: CSV for analysis.
    """
    if format == "csv":
        return StreamingResponse(
            iter_logs_as_csv(service_name=service_name, q=q),
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{service_name or "all"}_logs.csv"'
                )
            },
        )

    # default: text
    return StreamingResponse(
        iter_logs_as_text(service_name=service_name, q=q),
        media_type="text/plain",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{service_name or "all"}_logs.txt"'
            )
        },
    )


# ------------------------------------------------
# System summary for dashboard
# ------------------------------------------------
@router.get("/status")
def system_status():
    services = get_services()

    total = len(services)

    running = sum(
        1 for s in services if s["health_status"] == "healthy"
    )

    restarting = sum(
        1 for s in services if s["health_status"] == "restarting"
    )

    unhealthy = sum(
        1 for s in services if s["health_status"] == "unhealthy"
    )

    stopped = sum(
        1
        for s in services
        if s["health_status"] not in ["healthy", "restarting", "unhealthy"]
    )

    return {
        "total_services": total,
        "running": running,
        "restarting": restarting,
        "unhealthy": unhealthy,
        "stopped": stopped,
    }


# ------------------------------------------------
# Stream container logs (SSE)
# ------------------------------------------------
@router.get("/logs/{service}")
async def stream_logs(service: str):
    async def event_stream():
        async for line in stream_container_logs(service):
            yield line

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )
