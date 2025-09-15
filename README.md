# Sinko Backup Tool

Sinko is a flexible backup tool that supports both local and remote backups using rsync and SSH.

SINKO is a lightweight, open-source file backup tool designed with simplicity in mind. Inspired by the functionality of rsync, SINKO streamlines the process of synchronizing and backing up files across directories and systems. By focusing on the essential features you need to keep your files secure, SINKO eliminates the complexity often associated with robust backup tools. This straightforward approach makes SINKO an accessible solution for users of all skill levels, allowing you to safeguard your valuable data without getting bogged down in intricate configurations.

## Features

- Local backups using rsync
- Remote backups using SSH
- Configuration using a config file
- Command-line interface
- Extremely easy to use

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/sinko.git
   cd sinko
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To use Sinko, you need to create an EDN configuration file (e.g., `sinko.conf.edn`) with the following structure:

```edn
{:source ["/path/to/file1.txt"
         "/path/to/file2.txt"
         "/path/to/directory/file3.txt"]
 :destination "/path/to/backup/directory"}
```

Then, you can run the backup tool using the following command:

```
python -m source.main --sinko-conf /path/to/sinko.conf.edn
```

You can specify additional source files/directories via command line in two ways:

1. Multiple --source options:
```
python -m source.main --sinko-conf /path/to/sinko.conf.edn --source /extra/file1.txt --source /extra/dir2
```

2. Colon-delimited paths in a single --source option:
```
python -m source.main --sinko-conf /path/to/sinko.conf.edn --source "/extra/file1.txt:/extra/dir2:/extra/file3.txt"
```

The final backup source list will be a combination of sources from both the config file and command line options. When using colon-delimited paths, make sure to properly quote the argument if it contains special characters.

For the destination directory, the CLI option takes precedence over the config file if both are specified. You can override the destination directory from the config file using the --destination option:
```
python -m source.main --sinko-conf /path/to/sinko.conf.edn --destination /new/backup/path
```

Note that all CLI options except `--source` must be provided at most once. The following options cannot be duplicated:
- `--sinko-conf`
- `--destination`
- `--remote`
- `--log-level`

For remote backups, add the `--remote` flag:

```
python -m source.main --remote --sinko-conf /path/to/sinko.conf.edn
```

## Testing

To run the tests, use the following command:

```
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
