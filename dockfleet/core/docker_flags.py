def build_resource_flags(service_config: dict) -> list[str]:

    flags = []

    memory = service_config.get("memory")
    cpus = service_config.get("cpus")

    if memory:
        flags.extend(["--memory", str(memory)])

    if cpus:
        flags.extend(["--cpus", str(cpus)])

    return flags


def build_env_flags(service_config: dict) -> list[str]:

    flags = []

    env = service_config.get("environment")
    env_file = service_config.get("env_file")

    if env_file:
        flags.extend(["--env-file", env_file])
        return flags

    if env:
        for key, value in env.items():
            flags.extend(["-e", f"{key}={value}"])

    return flags


def build_port_flags(service_config: dict) -> list[str]:

    flags = []

    ports = service_config.get("ports", [])

    for port in ports:
        flags.extend(["-p", port])

    return flags