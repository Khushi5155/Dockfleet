import subprocess


class DockerManager:

    def create_network(self, name: str):
        subprocess.run(
            ["docker", "network", "create", name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def run_container(self, image, name, ports, network):

        command = [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "--network",
            network
        ]

        for port in ports:
            command.extend(["-p", port])

        command.append(image)

        subprocess.run(command)

    def stop_container(self, name):
        subprocess.run(["docker", "stop", name])

    def remove_container(self, name):
        subprocess.run(["docker", "rm", "-f", name])

    def list_containers(self):
        subprocess.run(["docker", "ps"])