from dockfleet.cli.config import load_config

config = load_config("examples/dockfleet.yaml")

print("CONFIG LOADED SUCCESSFULLY")
print(config)