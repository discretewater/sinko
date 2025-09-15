import os
import pytest
from unittest.mock import patch, mock_open
from source.main import read_edn_config, ConfigError, validate_config


def test_read_edn_config(sample_config, sample_files):
    config = read_edn_config(sample_config)
    assert isinstance(config, dict)
    assert "source" in config
    assert "destination" in config
    assert os.path.samefile(config["destination"], sample_files["dest_dir"])
    assert all(os.path.exists(f) for f in config["source"])


@pytest.mark.parametrize("is_remote", [True, False])
def test_backup_command(is_remote, sample_config):
    from typer.testing import CliRunner
    from source.main import app

    runner = CliRunner()
    args = ["--sinko-conf", sample_config]
    if is_remote:
        args.append("--remote")

    with patch("source.main.read_edn_config") as mock_read_config, patch(
        "source.main.RemoteSSHBackup"
    ) as mock_remote, patch("source.main.LocalRsyncBackup") as mock_local:

        mock_config = {
            "source": ["/test/file1.txt", "/test/file2.txt"],
            "destination": "/backup/dest",
        }
        mock_read_config.return_value = mock_config

        result = runner.invoke(app, args)
        assert result.exit_code == 0

        mock_read_config.assert_called_once_with(sample_config)

        if is_remote:
            mock_remote.assert_called_once_with(
                hostname="remote.server.com",
                username="your_username",
                password="your_password",
                remote_dir=mock_config["destination"],
                known_hosts=None,
            )
            mock_remote.return_value.backup_files.assert_called_once_with(
                mock_config["source"]
            )
        else:
            mock_local.assert_called_once_with(mock_config["destination"])
            mock_local.return_value.backup_files.assert_called_once_with(
                mock_config["source"]
            )


@pytest.mark.parametrize(
    "invalid_config,expected_error",
    [
        ({}, "Missing required key: source"),
        ({"source": "not_a_list"}, "'source' must be a list of file paths"),
        ({"source": []}, "Missing required key: destination"),
        ({"source": [], "destination": 42}, "'destination' must be a string path"),
        (
            {"source": [], "destination": "/nonexistent/path"},
            "Destination directory does not exist: /nonexistent/path",
        ),
    ],
)
def test_invalid_config_validation(invalid_config, expected_error):
    with pytest.raises(ConfigError, match=expected_error):
        validate_config(invalid_config)


def test_config_file_not_found():
    with pytest.raises(
        ConfigError, match="Configuration file not found: nonexistent.edn"
    ):
        read_edn_config("nonexistent.edn")


def test_invalid_edn_format():
    with patch("builtins.open", mock_open(read_data="{invalid: edn:")):
        with pytest.raises(ConfigError, match="Invalid EDN format:"):
            read_edn_config("dummy.edn")


def test_destination_exists(tmp_path):
    # Create a valid config with existing destination
    config = {"source": ["file1.txt"], "destination": str(tmp_path)}
    # Should not raise any exception
    validate_config(config)


def test_destination_not_exists():
    config = {
        "source": ["file1.txt"],
        "destination": "/definitely/not/exists/path",
    }
    with pytest.raises(ConfigError, match="Destination directory does not exist:"):
        validate_config(config)


def test_trailing_slash_removal(tmp_path):
    # Create test files and directories
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    test_file = source_dir / "test.txt"
    test_file.write_text("test content")

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    # Test config with trailing slashes
    config_content = f"""{{:source ["{str(source_dir)}/"]
                         :destination "{str(dest_dir)}/"}}\n"""

    config_path = tmp_path / "test_config.edn"
    config_path.write_text(config_content)

    # Read and verify config
    config = read_edn_config(str(config_path))

    # Verify trailing slashes were removed
    assert not config["source"][0].endswith("/")
    assert not config["source"][0].endswith("\\")
    assert not config["destination"].endswith("/")
    assert not config["destination"].endswith("\\")

    # Verify paths are still valid
    assert os.path.exists(config["source"][0])
    assert os.path.exists(config["destination"])


def test_main_missing_config_data():
    from typer.testing import CliRunner
    from source.main import app

    runner = CliRunner()

    with patch("source.main.read_edn_config") as mock_read_config:
        mock_read_config.return_value = {"source": []}  # Missing 'destination'

        result = runner.invoke(app, ["--sinko-conf", "dummy_path.edn"])

        assert result.exit_code == 1
        assert "Error: No destination specified in config or CLI." in result.stdout


def test_source_cli_option_single(sample_config):
    """Test single --source option"""
    from typer.testing import CliRunner
    from source.main import app

    runner = CliRunner()
    result = runner.invoke(
        app, ["--sinko-conf", sample_config, "--source", "/path/test1.txt"]
    )

    assert result.exit_code == 0


def test_source_cli_option_multiple(sample_config):
    """Test multiple --source options"""
    from typer.testing import CliRunner
    from source.main import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--sinko-conf",
            sample_config,
            "--source",
            "/path/test1.txt",
            "--source",
            "/path/test2.txt",
        ],
    )

    assert result.exit_code == 0


def test_source_cli_option_colon_delimited(sample_config):
    """Test colon-delimited --source option"""
    from typer.testing import CliRunner
    from source.main import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--sinko-conf",
            sample_config,
            "--source",
            "/path/test1.txt:/path/test2.txt:/path/test3.txt",
        ],
    )

    assert result.exit_code == 0


@pytest.mark.parametrize(
    "config_sources,cli_sources,expected",
    [
        (
            ["/config/file1.txt"],
            ["/cli/file2.txt"],
            ["/config/file1.txt", "/cli/file2.txt"],
        ),
        (
            ["/config/file1.txt"],
            ["/cli/file2.txt:/cli/file3.txt"],
            ["/config/file1.txt", "/cli/file2.txt", "/cli/file3.txt"],
        ),
        (
            [],
            ["/cli/file1.txt:/cli/file2.txt"],
            ["/cli/file1.txt", "/cli/file2.txt"],
        ),
    ],
)
def test_source_combination(sample_config, config_sources, cli_sources, expected):
    """Test combining sources from config and CLI"""
    from typer.testing import CliRunner
    from source.main import app

    runner = CliRunner()

    with patch("source.main.read_edn_config") as mock_read_config:
        mock_config = {"source": config_sources, "destination": "/backup/dest"}
        mock_read_config.return_value = mock_config

        args = ["--sinko-conf", sample_config]
        for src in cli_sources:
            args.extend(["--source", src])

        with patch("source.main.LocalRsyncBackup") as mock_backup:
            result = runner.invoke(app, args)
            assert result.exit_code == 0

            # Verify the combined sources were passed to backup
            mock_backup.return_value.backup_files.assert_called_once()
            actual_sources = mock_backup.return_value.backup_files.call_args[0][0]
            assert actual_sources == expected


def test_destination_cli_override(sample_config):
    """Test that CLI destination overrides config file destination"""
    from typer.testing import CliRunner
    from source.main import app

    runner = CliRunner()
    cli_destination = "/cli/backup/dest"

    with patch("source.main.read_edn_config") as mock_read_config, patch(
        "source.main.LocalRsyncBackup"
    ) as mock_backup, patch("os.path.exists") as mock_exists:

        # Setup mock config with a different destination
        mock_config = {
            "source": ["/test/file1.txt"],
            "destination": "/config/backup/dest",
        }
        mock_read_config.return_value = mock_config
        mock_exists.return_value = True  # Make path validation pass

        # Run with CLI destination
        result = runner.invoke(
            app, ["--sinko-conf", sample_config, "--destination", cli_destination]
        )

        assert result.exit_code == 0
        # Verify LocalRsyncBackup was created with CLI destination
        mock_backup.assert_called_once_with(cli_destination)


def test_destination_cli_duplicate(sample_config):
    """Test that providing destination CLI option multiple times fails"""
    from typer.testing import CliRunner
    from source.main import app
    import sys

    runner = CliRunner()

    with patch("source.main.read_edn_config") as mock_read_config, patch(
        "os.path.exists"
    ) as mock_exists, patch.object(
        sys,
        "argv",
        [
            "sinko",
            "--sinko-conf",
            sample_config,
            "--destination",
            "/dest1",
            "--destination",
            "/dest2",
        ],
    ):

        mock_config = {
            "source": ["/test/file1.txt"],
            "destination": "/config/backup/dest",
        }
        mock_read_config.return_value = mock_config
        mock_exists.return_value = True

        result = runner.invoke(
            app,
            [
                "--sinko-conf",
                sample_config,
                "--destination",
                "/dest1",
                "--destination",
                "/dest2",
            ],
        )

        assert result.exit_code == 1
        assert "Option '--destination' provided more than once" in result.stdout


@pytest.mark.parametrize(
    "option_name", ["--sinko-conf", "--destination", "--remote", "--log-level"]
)
def test_cli_option_duplicate(sample_config, option_name):
    """Test that providing CLI options multiple times fails"""
    from typer.testing import CliRunner
    from source.main import app
    import sys

    runner = CliRunner()

    with patch("source.main.read_edn_config") as mock_read_config, patch(
        "os.path.exists"
    ) as mock_exists, patch.object(
        sys, "argv", ["sinko", option_name, "value1", option_name, "value2"]
    ):

        mock_config = {
            "source": ["/test/file1.txt"],
            "destination": "/config/backup/dest",
        }
        mock_read_config.return_value = mock_config
        mock_exists.return_value = True

        # Prepare args based on option type
        if option_name == "--remote":
            args = ["--sinko-conf", sample_config, option_name, option_name]
        elif option_name == "--log-level":
            args = [
                "--sinko-conf",
                sample_config,
                option_name,
                "DEBUG",
                option_name,
                "INFO",
            ]
        else:
            args = [
                "--sinko-conf",
                sample_config,
                option_name,
                "value1",
                option_name,
                "value2",
            ]
            if option_name == "--sinko-conf":  # Remove the default --sinko-conf
                args = args[2:]

        result = runner.invoke(app, args)

        assert result.exit_code == 1
        assert f"Option '{option_name}' provided more than once" in result.stdout


def test_ensure_unique_options():
    """Test ensure_unique_options function with multiple options"""
    from source.main import ensure_unique_options
    import sys

    with patch.object(sys, "argv", ["sinko", "--opt1", "val1", "--opt2", "val2"]):
        # Should not raise any exception
        ensure_unique_options(["--opt1", "--opt2"])


def test_ensure_unique_options_with_duplicate():
    """Test ensure_unique_options function with duplicate options"""
    from source.main import ensure_unique_options
    import sys
    import typer
    import pytest

    with patch.object(sys, "argv", ["sinko", "--opt1", "val1", "--opt1", "val2"]):
        with pytest.raises(typer.Exit) as exc_info:
            ensure_unique_options(["--opt1", "--opt2"])
        assert exc_info.value.exit_code == 1


def test_ensure_unique_options_empty_list():
    """Test ensure_unique_options function with empty list"""
    from source.main import ensure_unique_options
    import sys

    with patch.object(sys, "argv", ["sinko", "--opt1", "val1"]):
        # Should not raise any exception with empty list
        ensure_unique_options([])


def test_sinko_conf_duplicate():
    """Test that providing multiple --sinko-conf options fails"""
    from typer.testing import CliRunner
    from source.main import app
    import sys

    runner = CliRunner()

    with patch("source.main.read_edn_config") as mock_read_config, patch(
        "os.path.exists"
    ) as mock_exists, patch.object(
        sys,
        "argv",
        ["sinko", "--sinko-conf", "config1.edn", "--sinko-conf", "config2.edn"],
    ):

        mock_exists.return_value = True

        result = runner.invoke(
            app, ["--sinko-conf", "config1.edn", "--sinko-conf", "config2.edn"]
        )

        assert result.exit_code == 1
        assert "Option '--sinko-conf' provided more than once" in result.stdout


def test_remote_duplicate():
    """Test that providing multiple --remote options fails"""
    from typer.testing import CliRunner
    from source.main import app
    import sys

    runner = CliRunner()

    with patch("source.main.read_edn_config") as mock_read_config, patch(
        "os.path.exists"
    ) as mock_exists, patch.object(
        sys,
        "argv",
        ["sinko", "--sinko-conf", "config.edn", "--remote", "--remote"],
    ):

        mock_config = {
            "source": ["/test/file1.txt"],
            "destination": "/backup/dest",
        }
        mock_read_config.return_value = mock_config
        mock_exists.return_value = True

        result = runner.invoke(
            app, ["--sinko-conf", "config.edn", "--remote", "--remote"]
        )

        assert result.exit_code == 1
        assert "Option '--remote' provided more than once" in result.stdout


def test_log_level_duplicate():
    """Test that providing multiple --log-level options fails"""
    from typer.testing import CliRunner
    from source.main import app
    import sys

    runner = CliRunner()

    with patch("source.main.read_edn_config") as mock_read_config, patch(
        "os.path.exists"
    ) as mock_exists, patch.object(
        sys,
        "argv",
        [
            "sinko",
            "--sinko-conf",
            "config.edn",
            "--log-level",
            "DEBUG",
            "--log-level",
            "INFO",
        ],
    ):

        mock_config = {
            "source": ["/test/file1.txt"],
            "destination": "/backup/dest",
        }
        mock_read_config.return_value = mock_config
        mock_exists.return_value = True

        result = runner.invoke(
            app,
            [
                "--sinko-conf",
                "config.edn",
                "--log-level",
                "DEBUG",
                "--log-level",
                "INFO",
            ],
        )

        assert result.exit_code == 1
        assert "Option '--log-level' provided more than once" in result.stdout


def test_source_deduplication(sample_config):
    """Test that duplicate sources are removed while preserving order"""
    from typer.testing import CliRunner
    from source.main import app

    runner = CliRunner()

    with patch("source.main.read_edn_config") as mock_read_config, patch(
        "source.main.LocalRsyncBackup"
    ) as mock_backup, patch("os.path.exists") as mock_exists:

        # Config with duplicate sources
        mock_config = {
            "source": ["/test/file1.txt", "/test/file2.txt", "/test/file1.txt"],
            "destination": "/backup/dest",
        }
        mock_read_config.return_value = mock_config
        mock_exists.return_value = True

        # CLI with some duplicates from config and between CLI options
        result = runner.invoke(
            app,
            [
                "--sinko-conf",
                sample_config,
                "--source",
                "/test/file1.txt:/test/file3.txt",
                "--source",
                "/test/file2.txt:/test/file3.txt",
            ],
        )

        assert result.exit_code == 0

        # Verify the combined sources were deduplicated
        mock_backup.return_value.backup_files.assert_called_once()
        actual_sources = mock_backup.return_value.backup_files.call_args[0][0]
        expected_sources = [
            "/test/file1.txt",
            "/test/file2.txt",
            "/test/file3.txt",
        ]
        assert actual_sources == expected_sources


def test_destination_required(sample_config):
    """Test that at least one destination must be provided"""
    from typer.testing import CliRunner
    from source.main import app

    runner = CliRunner()

    with patch("source.main.read_edn_config") as mock_read_config:
        # Config without destination
        mock_config = {"source": ["/test/file1.txt"]}
        mock_read_config.return_value = mock_config

        # Run without CLI destination
        result = runner.invoke(app, ["--sinko-conf", sample_config])

        assert result.exit_code == 1
        assert "Error: No destination specified in config or CLI" in result.stdout
