from dockfleet.core.docker import DockerManager
from dockfleet.health.status import (
    mark_service_running,
    mark_service_stopped
)


class Orchestrator:

    def __init__(self, config):
        self.config = config
        self.docker = DockerManager()
        self.network = "dockfleet_net"

    def up(self):

        print("Starting services...")

        self.docker.create_network(self.network)

        for name, svc in self.config.services.items():

            container_name = f"dockfleet_{name}"

            try:
                self.docker.run_container(
                    image=svc.image,
                    name=container_name,
                    ports=svc.ports,
                    network=self.network
                )

                mark_service_running(name)

                print(f"Started {name}")

            except Exception as e:
                print(f"Failed to start {name}: {e}")

    def down(self):

        print("Stopping services...")

        for name, svc in self.config.services.items():

            container_name = f"dockfleet_{name}"

            try:
                self.docker.remove_container(container_name)

                mark_service_stopped(name)

                print(f"Stopped {name}")

            except Exception as e:
                print(f"Failed to stop {name}: {e}")

    def ps(self):

        self.docker.list_containers()