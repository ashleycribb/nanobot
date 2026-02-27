"""CLI commands for nanobot."""

import typer
from nanobot import __logo__, __version__
from nanobot.cli.console import console
from nanobot.cli.agent import agent
from nanobot.cli.gateway import gateway
from nanobot.cli.onboard import onboard
from nanobot.cli.status import status
from nanobot.cli.channels import app as channels_app
from nanobot.cli.cron import app as cron_app
from nanobot.cli.provider import app as provider_app

app = typer.Typer(
    name="nanobot",
    help=f"{__logo__} nanobot - Personal AI Assistant",
    no_args_is_help=True,
)


def version_callback(value: bool):
    if value:
        console.print(f"{__logo__} nanobot v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True
    ),
):
    """nanobot - Personal AI Assistant."""
    pass


# Register commands
app.command()(onboard)
app.command()(gateway)
app.command()(agent)
app.command()(status)

# Register sub-apps
app.add_typer(channels_app, name="channels")
app.add_typer(cron_app, name="cron")
app.add_typer(provider_app, name="provider")


if __name__ == "__main__":
    app()
