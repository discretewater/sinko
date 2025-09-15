from .backup_interface import BackupInterface
import os
import paramiko
import subprocess
import logging
from typing import List, Dict
from datetime import datetime

# Set up logger
logger = logging.getLogger(__name__)


class LocalRsyncBackup(BackupInterface):
    """
    Implements local backup functionality using rsync.

    This class provides a local backup solution using the rsync utility for
    efficient file copying and synchronization. It handles both files and
    directories, preserving permissions and attributes while providing
    efficient delta transfers.

    Attributes:
        backup_dir (str): Destination directory for backups

    Requirements:
        - rsync must be installed on the system
        - Appropriate permissions for source and destination directories
    """

    def __init__(self, backup_dir: str):
        """
        Initialize the LocalRsyncBackup with a backup directory.

        Args:
            backup_dir (str): Path to the directory where backups will be stored
        """
        self.backup_dir = backup_dir

    def backup_files(self, file_list: List[str]) -> None:
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        for source in file_list:
            if not os.path.exists(source):
                logger.warning(f"Source not found: {source}")
                continue

            source_basename = os.path.basename(source.rstrip(os.sep))
            dest_path = os.path.join(self.backup_dir, source_basename)

            logger.info(f"Backing up {source} to {dest_path}")
            try:
                result = subprocess.run(
                    ["rsync", "-av", "--progress", source, self.backup_dir],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    logger.info(f"Successfully backed up {source} using rsync")
                else:
                    logger.error(f"Failed to backup {source}: {result.stderr}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Rsync error for {source}: {str(e)}")
            except FileNotFoundError:
                logger.error("rsync command not found - please install rsync")

    async def validate_backup(self, file_list: List[str]) -> Dict[str, bool]:
        """Validate that backed up files exist and match source"""
        validation_results = {}
        for file in file_list:
            source_path = file
            dest_path = os.path.join(self.backup_dir, os.path.basename(file))

            # Check if both files exist
            if not os.path.exists(source_path) or not os.path.exists(dest_path):
                validation_results[file] = False
                continue

            try:
                # Use rsync --checksum to compare files
                result = subprocess.run(
                    ["rsync", "--checksum", "--dry-run", source_path, dest_path],
                    capture_output=True,
                    text=True,
                )
                # If no output, files are identical
                validation_results[file] = len(result.stdout.strip()) == 0
            except subprocess.CalledProcessError:
                validation_results[file] = False

        return validation_results


class RemoteSSHBackup(BackupInterface):
    """
    Implements remote backup functionality using SSH/SFTP.

    This class provides secure remote backup capabilities using SSH for
    authentication and SFTP for file transfers. It supports both password
    and key-based authentication, with configurable host key verification
    for security.

    Attributes:
        hostname (str): Remote server hostname
        username (str): SSH username
        password (str): SSH password
        remote_dir (str): Destination directory on remote server
        port (int): SSH port number
        known_hosts (str): Path to known_hosts file
        testing (bool): Enable testing mode with relaxed security
        ssh (paramiko.SSHClient): SSH client instance

    Requirements:
        - paramiko library
        - Network connectivity to remote server
        - Valid SSH credentials
    """

    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        remote_dir: str,
        port: int = 22,
        known_hosts: str = None,
        testing: bool = False,
    ):
        """
        Initialize RemoteSSHBackup with connection parameters.

        Args:
            hostname (str): Remote server hostname
            username (str): SSH username
            password (str): SSH password
            remote_dir (str): Destination directory on remote server
            port (int, optional): SSH port number. Defaults to 22
            known_hosts (str, optional): Path to known_hosts file. Defaults to None
            testing (bool, optional): Enable testing mode. Defaults to False

        Note:
            In testing mode, host key verification is disabled
            In production, system host keys are used if known_hosts is None
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.remote_dir = remote_dir
        self.port = port
        self.known_hosts = known_hosts
        self.ssh = None
        self.testing = testing

    async def backup_files(self, file_list: List[str]) -> None:
        self.ssh = paramiko.SSHClient()
        logger.debug(f"Using known_hosts file: {self.known_hosts}")
        if self.testing:
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        elif self.known_hosts:
            self.ssh.load_host_keys(self.known_hosts)
            host_keys = self.ssh.get_host_keys()
            for hostname, keys in host_keys.items():
                logger.debug(f"Found host key for: {hostname}")
        else:
            self.ssh.load_system_host_keys()
            logger.debug("Loaded system host keys")

        ### check_ssh_server_status(self.hostname, self.port)

        try:
            # Set the policy for handling missing host keys. Consider using `paramiko.RejectPolicy()` in production.
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            logger.info(f"Initiating SSH connection to {self.hostname}:{self.port}")
            self.ssh.connect(
                self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                look_for_keys=False,
                allow_agent=False,
                timeout=20,
                banner_timeout=200,
                auth_timeout=20,
            )
            logger.debug("SSH connection established")
            sftp = self.ssh.open_sftp()
            logger.debug("SFTP connection opened")

            logger.info(f"Creating remote directory: {self.remote_dir}")
            try:
                sftp.mkdir(self.remote_dir)
                logger.debug(f"Remote directory created: {self.remote_dir}")
            except IOError as e:
                logger.debug(f"Remote directory exists: {self.remote_dir}")

            logger.info(f"Starting transfer of {len(file_list)} files")
            for file in file_list:
                if not os.path.exists(file):
                    logger.warning(f"Source file not found: {file}")
                    continue

                remote_path = f"{self.remote_dir}/{os.path.basename(file)}"
                try:
                    # Create remote directories if they don't exist
                    remote_dir = os.path.dirname(remote_path)
                    try:
                        sftp.mkdir(remote_dir)
                    except IOError:
                        pass  # Directory might already exist

                    logger.debug(f"Copying {file} to {remote_path}")
                    sftp.put(file, remote_path)
                    try:
                        sftp.stat(remote_path)
                        logger.info(f"Successfully transferred {file}")
                    except IOError as e:
                        logger.error(f"Failed to verify transfer of {file}: {e}")
                except Exception as e:
                    logger.error(f"Failed to backup {file}: {str(e)}")

        except Exception as e:
            logger.error(f"SSH connection failed: {str(e)}")
        finally:
            if self.ssh:
                self.ssh.close()
                logger.debug("SSH connection closed")

    async def validate_backup(self, file_list: List[str]) -> Dict[str, bool]:
        """Validate that backed up files exist and match source"""
        validation_results = {}
        self.ssh = paramiko.SSHClient()
        if self.testing:
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        elif self.known_hosts:
            self.ssh.load_host_keys(self.known_hosts)
        else:
            self.ssh.load_system_host_keys()

        try:
            self.ssh.connect(
                self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                look_for_keys=False,
                allow_agent=False,
            )
            sftp = self.ssh.open_sftp()

            for file in file_list:
                source_path = file
                remote_path = f"{self.remote_dir}/{os.path.basename(file)}"

                try:
                    # Check if remote file exists and compare contents
                    with open(source_path, "rb") as source_file, sftp.open(
                        remote_path, "rb"
                    ) as remote_file:
                        source_content = source_file.read()
                        remote_content = remote_file.read()
                        validation_results[file] = source_content == remote_content
                except (FileNotFoundError, IOError):
                    validation_results[file] = False

        except Exception as e:
            print(f"Debug: Error connecting to remote server: {str(e)}")
            for file in file_list:
                validation_results[file] = False
        finally:
            if self.ssh:
                self.ssh.close()

        return validation_results

    def close(self):
        """Close the SSH connection if it exists"""
        if self.ssh:
            self.ssh.close()
            self.ssh = None
