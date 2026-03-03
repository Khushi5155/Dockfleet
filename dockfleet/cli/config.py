from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import yaml

#healthcheck model
class HealthCheckConfig(BaseModel):
    type: str
    endpoint: Optional[str] = None
    interval: Optional[int] = 30

#Restart policy Enum
class RestartPolicy(str, Enum):
    always = "always"
    on_failure = "on-failure"
    never = "never"

#service model
class ServiceConfig(BaseModel):
    image: str
    ports: Optional[List[str]] = None
    healthcheck: Optional["HealthCheckConfig"] = None
    restart: RestartPolicy

#Root Config Model
class DockFleetConfig(BaseModel):
    services: Dict[str, ServiceConfig]

#load function
def load_config(path: str) -> DockFleetConfig:
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    return DockFleetConfig(**data)