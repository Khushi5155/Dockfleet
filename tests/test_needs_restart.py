import pytest
from sqlmodel import Session, select

from dockfleet.health.models import Service, init_db, engine
from dockfleet.health.status import update_service_health, needs_restart


def _create_service(
    name: str = "api",
    restart_policy: str = "always",
) -> Service:
    svc = Service(
        name=name,
        image="dummy-image",
        restart_policy=restart_policy,
        status="running",
    )
    with Session(engine) as session:
        session.add(svc)
        session.commit()
    return svc


def _get_service(name: str) -> Service:
    with Session(engine) as session:
        return session.exec(
            select(Service).where(Service.name == name)
        ).one()


def setup_function() -> None:
    """
    Simple per-test reset: drop + recreate all tables.

    NOTE: If your project already has a shared test_db fixture that
    handles this, prefer using that instead of setup_function.
    """
    # Recreate schema fresh for each test
    # (SQLModel doesn't have drop_all shortcut, so easiest in tests is
    # to recreate the file or use a temp DB; adapt if you already have
    # a better pattern in your suite.)
    init_db()


def test_needs_restart_after_three_failures_with_always_policy() -> None:
    init_db()
    _create_service(name="svc1", restart_policy="always")

    # simulate 3 consecutive unhealthy checks
    update_service_health("svc1", is_healthy=False, reason="fail 1")
    update_service_health("svc1", is_healthy=False, reason="fail 2")
    update_service_health("svc1", is_healthy=False, reason="fail 3")

    svc = _get_service("svc1")

    assert svc.consecutive_failures == 3
    assert svc.status == "unhealthy"
    assert needs_restart(svc) is True


def test_needs_restart_false_before_threshold() -> None:
    init_db()
    _create_service(name="svc2", restart_policy="always")

    # only 2 failures -> should NOT trigger restart yet
    update_service_health("svc2", is_healthy=False, reason="fail 1")
    update_service_health("svc2", is_healthy=False, reason="fail 2")

    svc = _get_service("svc2")

    assert svc.consecutive_failures == 2
    assert svc.status == "unhealthy"
    assert needs_restart(svc) is False


def test_needs_restart_respects_never_policy() -> None:
    init_db()
    _create_service(name="svc3", restart_policy="never")

    # even with 3 failures, never policy must block restart
    update_service_health("svc3", is_healthy=False, reason="fail 1")
    update_service_health("svc3", is_healthy=False, reason="fail 2")
    update_service_health("svc3", is_healthy=False, reason="fail 3")

    svc = _get_service("svc3")

    assert svc.consecutive_failures == 3
    assert svc.status == "unhealthy"
    assert needs_restart(svc) is False
