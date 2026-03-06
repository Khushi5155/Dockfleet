from sqlmodel import Session, select

from dockfleet.health.models import init_db, Service, engine
from dockfleet.health.services import seed_services
from dockfleet.health.status import mark_service_running, mark_service_stopped
from dockfleet.cli.config import load_config, DockFleetConfig


def test_mark_service_running_and_stopped(tmp_path):
    """
    End-to-end:
    - load config
    - seed services into SQLite
    - mark one service running, then stopped
    - verify status changes in DB
    """

    # 1) Fresh DB schema
    init_db()

    # 2) Config load
    config_path = "examples/dockfleet.yaml"
    config: DockFleetConfig = load_config(config_path)

    # 3) Seed services
    with Session(engine) as session:
        seed_services(config, session)

    service_name = list(config.services.keys())[0]

    # 4) Status initially "unknown"
    with Session(engine) as session:
        svc = session.exec(
            select(Service).where(Service.name == service_name)
        ).one()
        assert svc.status == "stopped"

    # 5) Mark running
    mark_service_running(service_name)

    # 6) Verify running in DB
    with Session(engine) as session:
        svc = session.exec(
            select(Service).where(Service.name == service_name)
        ).one()
        assert svc.status == "running"

    # 7) Mark stopped
    mark_service_stopped(service_name)

    # 8) Verify stopped in DB
    with Session(engine) as session:
        svc = session.exec(
            select(Service).where(Service.name == service_name)
        ).one()
        assert svc.status == "stopped"
