from typer.testing import CliRunner
from source.main import app


def test_backup(sample_config):
    runner = CliRunner()
    result = runner.invoke(app, ["--sinko-conf", sample_config])
    assert result.exit_code == 0
    assert result.stdout == "Backup completed successfully!\n"
