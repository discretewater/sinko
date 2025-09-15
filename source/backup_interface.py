from abc import ABC, abstractmethod
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BackupStatus:
    """
    Represents the status of a backup operation for a single file.

    Attributes:
        success (bool): Whether the backup operation was successful
        timestamp (datetime): When the backup operation occurred
        message (str): Status message or error description
        file_path (str): Path to the file that was backed up
        size_bytes (int): Size of the backed up file in bytes, defaults to 0
    """

    success: bool
    timestamp: datetime
    message: str
    file_path: str
    size_bytes: int = 0


class BackupInterface(ABC):
    """
    Abstract base class defining the interface for backup implementations.

    This interface provides a contract for different backup strategies (local, remote, etc.)
    to implement consistent backup functionality. Implementations must provide concrete
    methods for reading file lists, performing backups, and validating backup results.
    """

    @abstractmethod
    def backup_files(self, file_list: List[str]) -> None:
        """
        Performs the backup operation for the specified list of files.

        Creates a backup directory and copies the specified files into it.
        The backup directory may be timestamped or otherwise uniquely named
        to prevent overwriting previous backups.

        Args:
            file_list (List[str]): List of file paths to backup

        Raises:
            FileNotFoundError: If source files cannot be found
            IOError: If there are problems accessing source or destination
            OSError: If there are system-level errors during backup
        """
        pass

    @abstractmethod
    def validate_backup(self, file_list: List[str]) -> Dict[str, bool]:
        """
        Validates that backed up files exist and match their source.

        Compares source files against their backups to ensure integrity
        and completeness of the backup operation.

        Args:
            file_list (List[str]): List of source file paths to validate

        Returns:
            Dict[str, bool]: Mapping of file paths to validation results
                            True indicates successful validation
                            False indicates validation failure

        Raises:
            IOError: If there are problems accessing source or backup files
        """
        pass
