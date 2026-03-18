from datetime import datetime
from sqlmodel import Session, select
from .models import LogEvent, Service, engine

def store_log_line(
    service_name: str,
    message: str,
    level: str | None = None,
    source: str | None = None,
) -> None:
    """
    Store a single log metadata row for later search/analytics.

    - Looks up Service by name and attaches service_id + service_name.
    - Skips insert (with a warning) if the service is not present in the DB.
    - Intended callers:
        * CLI `dockfleet logs` path (sampling/aggregation).
        * SSE log streaming wrapper in the dashboard backend.
        * Orchestrator for structured events.
    """
    with Session(engine) as session:
        svc = session.exec(
            select(Service).where(Service.name == service_name)
        ).one_or_none()

        if svc is None:
            print(f"[logs] Service '{service_name}' not found in DB, skipping log")
            return

        event = LogEvent(
            service_id=svc.id,
            service_name=svc.name,
            created_at=datetime.utcnow(),
            level=level,
            message=message,
            source=source,
        )

        session.add(event)
        session.commit()
        