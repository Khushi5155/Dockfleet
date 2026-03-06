from sqlmodel import Session, select
from .models import Service, engine
from datetime import datetime

def mark_service_running(name: str) -> None:
    _update_status(name, "running", set_last_health=True)

def mark_service_stopped(name: str) -> None:
    _update_status(name, "stopped", set_last_health=False)

def _update_status(name: str, new_status: str, set_last_health: bool = False) -> None:
    # 1) Session open with context manager
    with Session(engine) as session:
        # 2) Service row find karo by name
        existing = session.exec(
            select(Service).where(Service.name == name)
        ).one_or_none()

        # 3) Not found → silently return (ya warning log)
        if existing is None:
            print(f"[status] Service '{name}' not found in DB, skipping status update")
            return

        # 4) Status change + optional last_health_check
        existing.status = new_status

        if set_last_health:
            existing.last_health_check = datetime.utcnow()

        # 5) Commit the change
        session.add(existing)
        session.commit()
