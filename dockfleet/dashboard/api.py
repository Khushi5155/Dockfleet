from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="DockFleet Dashboard API",
    version="0.1.0"
)

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/services")
def list_services():
    # Dummy data for now
    return [
        {"name": "api", "status": "running"},
        {"name": "worker", "status": "stopped"}
    ]


@app.get("/")
def root():
    return {"message": "DockFleet Dashboard API is running"}
    