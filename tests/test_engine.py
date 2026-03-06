from dockfleet.core.orchestrator import Orchestrator


# -----------------------------
# FAKE CLASSES
# -----------------------------

class FakeService:
    def __init__(self, name, image, ports):
        self.name = name
        self.image = image
        self.ports = ports


class FakeApp:
    name = "testapp"
    vps = "dummy"

    services = [
        FakeService("web", "nginx:latest", [80]),
        FakeService("api", "python:3.11", [5000]),
    ]


class FakeDocker:
    def __init__(self):
        self.network_created = None
        self.containers_started = []
        self.containers_removed = []
        self.ps_called = False

    def create_network(self, name):
        self.network_created = name

    def run_container(self, image, name, ports, network):
        self.containers_started.append(
            {
                "image": image,
                "name": name,
                "ports": ports,
                "network": network,
            }
        )

    def remove_container(self, name):
        self.containers_removed.append(name)

    def list_containers(self, app_name):
        self.ps_called = True
        return (
            "testapp_web|nginx:latest|Up 10 seconds\n"
            "testapp_api|python:3.11|Exited (1)"
        )


class FakeSSH:
    def __init__(self):
        self.last_command = None

    def run(self, command):
        self.last_command = command


# -----------------------------
# TEST UP
# -----------------------------

def test_up_creates_network_and_containers():

    docker = FakeDocker()

    orchestrator = Orchestrator(
        app=FakeApp(),
        docker_adapter=docker,
        ssh_client=FakeSSH()
    )

    orchestrator.up()

    assert docker.network_created == "testapp_net"

    assert len(docker.containers_started) == 2

    assert docker.containers_started[0]["name"] == "testapp_web"
    assert docker.containers_started[1]["name"] == "testapp_api"


# -----------------------------
# TEST DOWN
# -----------------------------

def test_down_removes_containers_and_network():

    docker = FakeDocker()
    ssh = FakeSSH()

    orchestrator = Orchestrator(
        app=FakeApp(),
        docker_adapter=docker,
        ssh_client=ssh
    )

    orchestrator.down()

    assert "testapp_web" in docker.containers_removed
    assert "testapp_api" in docker.containers_removed

    assert ssh.last_command == "docker network rm testapp_net || true"


# -----------------------------
# TEST PS
# -----------------------------

def test_ps_lists_containers():

    docker = FakeDocker()

    orchestrator = Orchestrator(
        app=FakeApp(),
        docker_adapter=docker,
        ssh_client=FakeSSH()
    )

    output = orchestrator.ps()

    assert docker.ps_called is True
    assert "testapp_web" in output
    assert "testapp_api" in output