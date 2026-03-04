from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import time
import json

router = APIRouter()

# Setup templates
templates = Jinja2Templates(directory="dockfleet/dashboard/templates")

class Service(BaseModel):
    name: str
    status: str
    cpu: int          
    memory: int       
    uptime: str
    restart_count: int
    health_status: str



@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/", response_class=HTMLResponse)
def dashboard_home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@router.get("/services", response_model=List[Service])
def list_services():
    return [
        Service(
            name="api",
            status="running",
            cpu=18,
            memory=320,
            uptime="4h 12m",
            restart_count=1,
            health_status="healthy"
        ),
        Service(
            name="worker",
            status="restarting",
            cpu=5,
            memory=150,
            uptime="12m",
            restart_count=5,
            health_status="degraded"
        ),
        Service(
            name="scheduler",
            status="stopped",
            cpu=0,
            memory=0,
            uptime="0m",
            restart_count=2,
            health_status="unhealthy"
        )
    ]


@router.get("/logs/{service}")
def stream_service_logs(service: str):

    def event_generator():
        counter = 1
        while True:
            log_data = {
                "service": service,
                "message": f"Log entry {counter} from {service}",
                "level": "INFO"
            }

            yield f"data: {json.dumps(log_data)}\n\n"
            counter += 1
            time.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
    

@router.get("/status")
def system_status():
    services = list_services()

    total = len(services)
    running = sum(1 for s in services if s.status == "running")
    unhealthy = sum(1 for s in services if s.health_status != "healthy")

    return {
        "total_services": total,
        "running": running,
        "unhealthy": unhealthy
    }

    