class FileListReader:
    """
    Reads and parses a file containing a list of files to be backed up.

    This class handles reading a text file that contains a list of file paths,
    one per line, and returns them as a list of strings.

    Attributes:
        file_path (str): Path to the file containing the list of files to backup
    """

    def __init__(self, file_path: str):
        """
        Initialize the FileListReader with a path to the file list.

        Args:
            file_path (str): Path to the file containing the list of files
        """
        self.file_path = file_path

    def read_file_list(self) -> list[str]:
        """
        Reads and returns the list of files from the specified file.

        Returns:
            list[str]: List of file paths read from the file
                      Returns empty list if file is not found

        Note:
            Each line in the file should contain a single file path
            Empty lines and whitespace are stripped
        """
        try:
            with open(self.file_path, "r") as file:
                return file.read().splitlines()
        except FileNotFoundError:
            print(f"File {self.file_path} not found.")
            return []
