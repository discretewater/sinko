import pytest
from pathlib import Path
from source.backup import RemoteSSHBackup
import paramiko


@pytest.mark.asyncio
async def test_remote_backup_connection(sftpserver):
    """Test that we can connect to the test SSH server and backup a file."""
    content = "test content\n"
    test_file = Path("test.txt")

    with sftpserver.serve_content({"": {"readme.txt": "Please upload files here"}}):
        backup = RemoteSSHBackup(
            hostname=sftpserver.host,
            username="user",
            password="pass",
            remote_dir="/",
            port=sftpserver.port,
        )

        try:
            # Create and write to the test file
            test_file.write_text(content)

            # Perform the backup
            await backup.backup_files([str(test_file)])

            # Verify file exists in remote directory with correct content using Paramiko
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    sftpserver.host,
                    port=sftpserver.port,
                    username="user",
                    password="pass",
                )

                with ssh.open_sftp() as sftp:
                    with sftp.open("test.txt", "r") as remote_file:
                        remote_content = remote_file.read().decode()

                assert (
                    remote_content == content
                ), f"Expected content: {content}, but got: {remote_content}"
        finally:
            backup.close()
            if test_file.exists():
                test_file.unlink()  # Clean up the test file


@pytest.mark.asyncio
async def test_remote_backup_validation(sftpserver, tmp_path):
    """Test backup validation on remote server."""
    # Create test files with content
    files = []
    file_contents = {}
    for i in range(3):
        test_file = tmp_path / f"test{i}.txt"
        content = f"test content {i}\n"
        test_file.write_text(content)
        files.append(str(test_file))
        file_contents[f"test{i}.txt"] = content

    with sftpserver.serve_content({"": {"readme.txt": "Please upload files here"}}):
        backup = RemoteSSHBackup(
            hostname=sftpserver.host,
            username="user",
            password="pass",
            remote_dir="/",
            port=sftpserver.port,
            testing=True,
        )

        try:
            # Perform backup
            await backup.backup_files(files)

            # Validate backup
            validation_results = await backup.validate_backup(files)
            assert all(validation_results.values())

            # Additional verification using Paramiko
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    sftpserver.host,
                    port=sftpserver.port,
                    username="user",
                    password="pass",
                )

                with ssh.open_sftp() as sftp:
                    for file in files:
                        filename = Path(file).name
                        with sftp.open(filename, "r") as remote_file:
                            remote_content = remote_file.read().decode()
                            assert remote_content == file_contents[filename]
        finally:
            backup.close()
