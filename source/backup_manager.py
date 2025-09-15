import os
import shutil
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Manages backup operations by implementing the BackupInterface.

    This class handles the creation of timestamped backup directories and
    coordinates the copying of files to the backup location. It provides
    a high-level interface for backup operations while handling the details
    of backup organization and file management.

    Attributes:
        backup_dir (str): Base directory where backups will be stored
    """

    def __init__(self, backup_dir: str):
        """
        Initialize the BackupManager with a backup directory.

        Args:
            backup_dir (str): Path to the directory where backups will be stored
        """
        self.backup_dir = backup_dir

    def backup_files(self, file_list: list[str]) -> None:
        backup_dir_name = f"backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        backup_dir_path = os.path.join(
            self.backup_dir.rstrip(os.sep), backup_dir_name
        )
        os.makedirs(backup_dir_path)

        for file in file_list:
            try:
                shutil.copy(file, backup_dir_path)
                logger.info(f"Successfully backed up file: {file}")
            except FileNotFoundError:
                logger.error(f"File not found: {file}")
