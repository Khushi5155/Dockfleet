from datetime import datetime
from typing import Optional
from sqlmodel import Session, select
from .models import Service, engine

def mark_service_running(name: str) -> None:
    _update_status(name, "running", set_last_health=True)

def mark_service_stopped(name: str) -> None:
    _update_status(name, "stopped", set_last_health=False)

def _update_status(
    name: str,
    new_status: str,
    set_last_health: bool = False,
) -> None:
    """Low-level helper to flip status for a service by name."""
    with Session(engine) as session:
        existing = session.exec(
            select(Service).where(Service.name == name)
        ).one_or_none()

        if existing is None:
            print(
                f"[status] Service '{name}' not found in DB, skipping status update"
            )
            return

        existing.status = new_status

        if set_last_health:
            existing.last_health_check = datetime.utcnow()

        session.add(existing)
        session.commit()

def update_service_health(
    name: str,
    is_healthy: bool,
    reason: Optional[str] = None,
) -> None:
    """
    Update Service row after a health check.

    - If healthy:
        status = "running"
        last_health_check updated
        restart_count unchanged
        consecutive_failures reset to 0
    - If unhealthy:
        status = "unhealthy"
        last_health_check updated
        restart_count++
        consecutive_failures++
        last_failure_reason stored (if provided)
    """
    with Session(engine) as session:
        svc = session.exec(
            select(Service).where(Service.name == name)
        ).one_or_none()

        if svc is None:
            print(f"[health] Service '{name}' not found in DB")
            return

        now = datetime.utcnow()
        svc.last_health_check = now

        if is_healthy:
            # health OK -> treat as running service
            svc.status = "running"
            # if we were failing before, reset the streak
            svc.consecutive_failures = 0
            # restart_count unchanged here
        else:
            svc.status = "unhealthy"
            svc.restart_count += 1
            svc.consecutive_failures += 1
            if reason:
                svc.last_failure_reason = reason

        session.add(svc)
        session.commit()

def needs_restart(service: Service) -> bool:
    """
    Decide if a service should be restarted based on failure streak
    and restart_policy.
    Rules:
    - If restart_policy == "never" -> never restart.
    - Otherwise, restart if consecutive_failures >= 3.
    """
    # policies: "always", "on-failure", "never"
    if service.restart_policy == "never":
        return False

    if service.consecutive_failures < 3:
        return False

    # For "always" and "on-failure", once we have 3 consecutive
    # unhealthy checks, this service is eligible for restart.
    return True
