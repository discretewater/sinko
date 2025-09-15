import pytest
import os
from datetime import datetime


@pytest.fixture
def backup_status_data():
    return {
        "success": True,
        "timestamp": datetime.now(),
        "message": "Backup successful",
        "file_path": "/path/to/backup/file",
        "size_bytes": 1024,
    }


@pytest.fixture
def sample_files(tmp_path):
    # Create temporary test files
    files = []
    dest_dir = tmp_path / "backup_dest"
    dest_dir.mkdir()

    for i in range(3):
        file_path = tmp_path / f"file{i}.txt"
        file_path.write_text(f"Test content {i}")
        files.append(str(file_path))

    return {"files": files, "dest_dir": str(dest_dir)}


@pytest.fixture
def sample_config(tmp_path, sample_files):
    # Create local_backup directory
    local_backup_dir = tmp_path / "local_backup"
    local_backup_dir.mkdir(exist_ok=True)

    config_path = local_backup_dir / "test_config.edn"
    config_content = f"""{{:source [{", ".join(f'"{f}"' for f in sample_files['files'])}]
                         :destination "{sample_files['dest_dir']}"}}"""
    config_path.write_text(config_content)
    return str(config_path)
