from __future__ import annotations
from typing import Any, Dict, List
from sqlmodel import Session, select
from .models import Service, engine


def get_all_services() -> list[Service]:
    """
    Low-level helper: return all Service rows from SQLite.
    Dashboard/API layer can either use these ORM objects directly
    or call get_services_for_dashboard() for JSON-ready dicts.
    """
    with Session(engine) as session:
        services = session.exec(select(Service)).all()
    return services


def get_services_for_dashboard() -> list[dict[str, Any]]:
    """
    High-level helper: return services as plain dicts suitable
    for the /services dashboard API response.
    These dicts can be easily enriched with orchestrator stats
    (CPU, memory, uptime) before sending to the frontend.
    """
    services = get_all_services()

    result: list[dict[str, Any]] = []
    for svc in services:
        result.append(
            {
                "name": svc.name,
                "status": svc.status,
                "restart_count": svc.restart_count,
                "last_health_check": svc.last_health_check,
                # extra health-engine fields that may be useful to the UI
                "consecutive_failures": svc.consecutive_failures,
                "last_failure_reason": svc.last_failure_reason,
            }
        )
    return result
