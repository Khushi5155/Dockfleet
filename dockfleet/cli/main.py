import typer
from pathlib import Path
from pydantic import ValidationError

from dockfleet.cli.config import load_config
from dockfleet.core.orchestrator import Orchestrator
from dockfleet.health.seed import bootstrap_from_path

app = typer.Typer()

validate_app = typer.Typer()
app.add_typer(validate_app, name="validate")


@validate_app.callback(invoke_without_command=True)
def validate(path: Path = typer.Argument("dockfleet.yaml")):
    """Validate a DockFleet configuration file."""
    try:
        load_config(path)
        typer.echo("Config valid")

    except ValidationError as e:
        typer.echo("Config validation failed")
        for err in e.errors():
            location = " -> ".join(str(x) for x in err["loc"])
            typer.echo(f"{location}: {err['msg']}")
        raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Unexpected error: {e}")
        raise typer.Exit(code=1)


@app.command()
def seed(path: Path = typer.Argument("dockfleet.yaml")):
    """Initialize DB and seed services."""
    try:
        typer.echo("Seeding services into DB...")

        bootstrap_from_path(str(path))

        typer.echo("Seeding complete")

    except Exception as e:
        typer.echo(f"Seeding failed: {e}")
        raise typer.Exit(code=1)


@app.command()
def up(path: Path = typer.Argument("dockfleet.yaml")):
    """Start services."""
    try:
        config = load_config(path)

        orch = Orchestrator(config)

        orch.up()

    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)


@app.command()
def down(path: Path = typer.Argument("dockfleet.yaml")):
    """Stop services."""
    try:
        config = load_config(path)

        orch = Orchestrator(config)

        orch.down()

    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)


@app.command()
def ps():
    """List running containers."""
    try:
        orch = Orchestrator(config=None)

        orch.ps()

    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()