from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, config, field_validator
from typing import Optional, List, Dict
import yaml

#healthcheck model
class HealthCheckConfig(BaseModel):
    type: str
    endpoint: Optional[str] = None
    interval: Optional[int] = None

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

#Resource limits model
class ResourcesConfig(BaseModel):
    image:str
    restart: str

    ports: Optional[List[str]] = None
    healthcheck: Optional[HealthCheckConfig] = None
    resources: Optional[ResourcesConfig] = None
    depends_on: Optional[List[str]] = None
    environment: Optional[List[str]] = None

    @field_validator("restart")
    @classmethod
    def validate_restart_policy(cls, value):
        allowed = {"always", "on-failure", "never"}
        if value not in allowed:
            raise ValueError(f"restart must be one of {allowed}")
        return value
    
#YAML loader
def load_config(path: Path) -> DockFleetConfig:
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    if not data:
        raise ValueError("Config file is empty")

    return DockFleetConfig(**data)