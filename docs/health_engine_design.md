## 1. Responsibilities
- track service health status
- auto-restart on failures
- store restart history
- sync with YAML config (ServiceConfig)

## 2. Config → Service mapping
- DockFleetConfig.services[name] → Service.name
- ServiceConfig.image → Service.image
- ServiceConfig.restart → Service.restart_policy
- ServiceConfig.ports → Service.ports_raw
- ServiceConfig.healthcheck → Service.healthcheck_raw

## 3. Functions
### from_config(config: DockFleetConfig) -> list[Service]
- input: parsed YAML config
- output: list of Service objects (not yet in DB)
- steps:
  - loop over config.services.items()
  - map fields
  - set runtime defaults (status, restart_count, etc.)

### seed_services(config, session)
- input: config + DB session
- behavior: insert Service rows if not already present
- idempotent: safe to call multiple times
