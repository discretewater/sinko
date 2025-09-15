from .backup import LocalRsyncBackup, RemoteSSHBackup
import os
import sys
import edn_format
import logging
from datetime import datetime
import typer
from typing import Optional, List


def setup_logging(level=logging.ERROR):
    """Setup logging configuration"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(
        log_dir, f"sinko_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )
    return logging.getLogger(__name__)


class ConfigError(Exception):
    """Configuration related errors"""

    pass


def validate_config(config: dict) -> None:
    """Validate configuration structure and content"""
    # First check if source exists before checking its type
    if "source" not in config:
        raise ConfigError("Missing required key: source")

    # Then validate source type
    if not isinstance(
        config["source"], (list, edn_format.immutable_list.ImmutableList)
    ):
        raise ConfigError("'source' must be a list of file paths")

    # Then check destination exists
    if "destination" not in config:
        raise ConfigError("Missing required key: destination")

    # Validate destination type and existence
    if not isinstance(config["destination"], str):
        raise ConfigError("'destination' must be a string path")

    # Check if destination directory exists
    if not os.path.exists(config["destination"]):
        raise ConfigError(
            f"Destination directory does not exist: {config['destination']}"
        )


def read_edn_config(config_path):
    try:
        with open(config_path, "r") as file:
            content = file.read()
            raw_config = edn_format.loads(content)
            # Convert EDN keywords to regular strings
            config = {}
            for k, v in raw_config.items():
                # Convert Keyword objects to strings by removing the leading ':'
                key = str(k)[1:] if hasattr(k, "name") else str(k).replace(":", "")
                # Convert ImmutableList to regular list if needed
                if key == "source":
                    config[key] = [path.rstrip(os.sep) for path in list(v)]
                else:
                    config[key] = v.rstrip(os.sep) if isinstance(v, str) else v
            validate_config(config)
            return config
    except FileNotFoundError:
        raise ConfigError(f"Configuration file not found: {config_path}")
    except edn_format.EDNDecodeError as e:
        raise ConfigError(f"Invalid EDN format: {str(e)}")


app = typer.Typer(help="Backup files using local or remote storage")


def ensure_unique_option(option_name: str):
    # Count occurrences of the option in sys.argv
    occurrences = sum(1 for i, arg in enumerate(sys.argv) if arg == option_name)
    if occurrences > 1:
        typer.echo(
            f"Error: Option '{option_name}' provided more than once.", err=True
        )
        raise typer.Exit(code=1)


def ensure_unique_options(option_names: list[str]) -> None:
    """Ensure each option in the list appears at most once in sys.argv"""
    for option_name in option_names:
        ensure_unique_option(option_name)


@app.command()
def backup(
    sinko_conf: str = typer.Option(..., help="Path to the EDN configuration file"),
    source: List[str] = typer.Option(
        None, help="Additional source files/directories to backup"
    ),
    destination: Optional[str] = typer.Option(
        None, help="Backup destination directory (overrides config file)"
    ),
    remote: bool = typer.Option(False, help="Use remote backup instead of local"),
    log_level: str = typer.Option(
        "ERROR", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    ),
) -> None:
    """
    Backup files according to the configuration in the EDN file.
    """
    # Setup logging
    logger = setup_logging(getattr(logging, log_level.upper()))

    # Check for duplicate options
    ensure_unique_options(
        ["--sinko-conf", "--destination", "--remote", "--log-level"]
    )

    # Read the configuration
    try:
        config = read_edn_config(sinko_conf)
    except ConfigError as e:
        typer.secho(f"Configuration error: {str(e)}", fg=typer.colors.RED)
        raise typer.Exit(1)

    # Combine sources from config file and CLI options
    config_sources = config.get("source", [])

    # Process CLI sources - split colon-delimited paths
    cli_sources = []
    if source:
        for src in source:
            cli_sources.extend(src.split(":"))

    # Combine sources while preserving order and removing duplicates
    seen = set()
    file_list = []
    for item in config_sources + cli_sources:
        if item not in seen:
            seen.add(item)
            file_list.append(item)
    backup_destination = destination if destination else config.get("destination", "")

    if not backup_destination:
        typer.secho(
            "Error: No destination specified in config or CLI.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    if not file_list:
        typer.secho(
            "Error: No source files specified in config or CLI.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    if remote:
        # Use remote SSH backup
        # For production, system host keys will be used
        backup = RemoteSSHBackup(
            hostname="remote.server.com",
            username="your_username",
            password="your_password",
            remote_dir=backup_destination,
            known_hosts=None,  # Will use system host keys
        )
    else:
        # Use local rsync backup
        backup = LocalRsyncBackup(backup_destination)

    try:
        backup.backup_files(file_list)
        typer.secho("Backup completed successfully!", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Backup failed: {str(e)}", fg=typer.colors.RED)
        raise typer.Exit(1)


def main():
    app()


if __name__ == "__main__":
    main()
