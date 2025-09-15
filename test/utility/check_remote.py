import asyncssh


async def check_remote_file(server_info, remote_path, expected_content):
    """
    Check whether a specific path exists on the server and verify that the path pointing file's content
    is equal to a specific value.

    :param ssh_server: Fixture providing SSH server information. # FIXME
    :param remote_path: The path to check on the server.
    :param expected_content: The expected content of the file.
    :return: True if the path exists and the content matches, False otherwise.
    """
    hostname = server_info["host"]
    port = server_info["port"]
    username = "test"
    password = "test"

    try:
        async with asyncssh.connect(
            hostname,
            port=port,
            username=username,
            password=password,
            known_hosts=server_info.get("known_hosts"),
            client_keys=None,
        ) as conn:
            # Check if the file exists
            try:
                result = await conn.run(f"test -f {remote_path}", check=True)
                if result.exit_status != 0:
                    return False

                # Read the file content
                result = await conn.run(f"cat {remote_path}", check=True)
                file_content = result.stdout

                # Verify the content (without stripping to preserve exact content)
                return file_content == expected_content
            except Exception:
                return False
    except Exception:
        return False
