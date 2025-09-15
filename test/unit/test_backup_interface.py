from source.backup_interface import BackupStatus
import pytest


def test_backup_status_creation(backup_status_data):
    backup_status = BackupStatus(**backup_status_data)
    assert backup_status.success == backup_status_data["success"]
    assert backup_status.timestamp == backup_status_data["timestamp"]
    assert backup_status.message == backup_status_data["message"]
    assert backup_status.file_path == backup_status_data["file_path"]
    assert backup_status.size_bytes == backup_status_data["size_bytes"]
