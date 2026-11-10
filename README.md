# PrimeToolv3

> A lightweight, remotely maintained Python CLI for downloading, managing and executing standalone Python encryption and decryption scripts.

PrimeToolv3 provides a simple terminal interface for running a remotely maintained Python encryption and decryption tool without requiring users to manually download scripts, manage virtual environments or install dependencies.

The CLI is distributed through **PyPI**, while the actual tool is independently maintained and distributed through **GitHub Releases**.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Execution Workflow](#execution-workflow)
- [Version Management](#version-management)
- [Local Storage](#local-storage)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Security](#security)
- [Development Roadmap](#development-roadmap)
- [Contributing](#contributing)
- [License](#license)

## Overview

PrimeToolv3 consists of three independently managed components:

1. **CLI Package:** A lightweight Python package published on PyPI.
2. **GitHub Repository:** A single repository containing the CLI source code, converter source code and release configuration.
3. **Local Converter Environment:** A dedicated Python virtual environment managed automatically by the CLI.

The CLI acts as a launcher and environment manager. It retrieves the latest converter release, prepares its runtime environment and executes the converter.

### Primary Objective

The intended consumer experience is deliberately simple:

```bash
python -m pip install prime-tool-v3
```

Once installed:

```bash
prime-tool-v3 run
```

Everything else is handled automatically.

## Architecture

The project uses a single GitHub repository as its source of truth.

The CLI package and converter are distributed through separate channels.

```text
                  DEVELOPER
                      |
                      v
             GITHUB REPOSITORY
                      |
          +-----------+-----------+
          |                       |
          v                       v
      CLI SOURCE              CONVERTER
          |                       |
          v                       v
        PyPI               GITHUB RELEASES
          |                       |
          +-----------+-----------+
                      |
                      v
                   CONSUMER
                      |
                      v
             pip install prime-tool-v3
                      |
                      v
               prime-tool-v3 run
                      |
                      v
             Remote version check
                      |
                      v
             Download converter
                      |
                      v
              Prepare local venv
                      |
                      v
             Resolve dependencies
                      |
                      v
              Request permission
                      |
                      v
              Execute converter
```

### Component Responsibilities

| Component | Responsibilities |
|---|---|
| PyPI CLI | Command handling, release discovery, downloads, caching, environment management and execution |
| GitHub | Source code management and converter release distribution |
| Local environment | Converter script, dependencies and runtime isolation |

The CLI uses the consumer's existing Python installation. It does not require a separate environment of its own.

A dedicated virtual environment is created exclusively for the converter.

## Features

### CLI Management

- Simple terminal interface.
- Independent CLI and converter versioning.
- Automatic remote release discovery.
- Local converter caching.
- Automatic converter updates.

### Environment Management

- Automatic virtual environment creation.
- Dependency detection.
- User confirmation before installing dependencies.
- Isolated dependency installation.
- Reuse of the existing converter environment.

### Execution

- Direct execution through the dedicated virtual environment.
- Interactive terminal input and output.
- Standard output and error propagation.
- Converter exit-code propagation.

### Cross-Platform Support

Designed to support:

- Linux
- macOS
- Windows

## Installation

Install the CLI package using pip:

```bash
python -m pip install prime-tool-v3
```

This installs the CLI and registers the `prime-tool-v3` terminal command.

No additional manual setup is required.

> **Note:** The package is under development. Installation instructions will become applicable once the initial PyPI release is published.

## Usage

### Available Commands

| Command | Description |
|---|---|
| `prime-tool-v3 run` | Check, prepare and execute the converter |
| `prime-tool-v3 update` | Download the latest converter release |
| `prime-tool-v3 version` | Display CLI and converter versions |
| `prime-tool-v3 clean` | Remove locally managed converter resources |

### Run the Converter

```bash
prime-tool-v3 run
```

The CLI checks for updates, prepares the runtime environment and launches the converter.

### Update the Converter

```bash
prime-tool-v3 update
```

Retrieves and caches the latest available converter release without requiring a new CLI installation.

### Display Versions

```bash
prime-tool-v3 version
```

Displays the installed CLI version and the currently cached converter version.

### Clean Local Resources

```bash
prime-tool-v3 clean
```

Removes all locally managed converter resources, including:

- Downloaded converter scripts.
- Dedicated virtual environment.
- Cached metadata.
- Application logs.
- Other managed resources.

This operation does not uninstall the CLI package or modify the consumer's global Python installation.

### Update the CLI

CLI updates are managed independently through pip:

```bash
python -m pip install --upgrade prime-tool-v3
```

## Execution Workflow

When the consumer executes:

```bash
prime-tool-v3 run
```

The CLI performs the following operations.

### 1. Initialize Local Storage

Creates the application directory and required sub-directories if they do not already exist.

### 2. Check Remote Version

Retrieves the latest converter release information from the public GitHub Releases API.

Compares the remote version against the locally cached version.

- No cached version: Download the latest release.
- Newer remote version: Update the local converter.
- Matching versions: Reuse the cached converter.
- Network unavailable: Fall back to a previously validated local release, if available.

Every normal execution performs a remote version check.

### 3. Prepare Virtual Environment

If the dedicated converter environment does not exist, the CLI:

- Detects a compatible Python interpreter.
- Creates a virtual environment.
- Configures the environment for converter execution.

The environment is reused across subsequent executions.

### 4. Resolve Dependencies

Reads the `requirements.txt` distributed with the converter release.

Checks whether the required dependencies are available in the dedicated environment.

If installation or modification is necessary, the CLI requests permission:

```text
Dependency installation required.

The following packages need to be installed:

  - 

Install dependencies and continue? [y/n]:
```

- `y`: Install the required dependencies and continue.
- `n`: Abort execution without launching the converter.

Dependencies are never installed into the consumer's global Python environment.

### 5. Execute Converter

Launches the downloaded converter using the Python interpreter inside the dedicated virtual environment.

The CLI preserves the converter's standard input, standard output and standard error streams.

The converter retains control over its own interactive inputs, processing and output.

The CLI also propagates the converter's exit code.

## Version Management

PrimeToolv3 maintains two independent version numbers.

### CLI Version

Managed through PyPI.

Example:

```text
0.1.0
0.2.0
0.3.0
```

Updated independently using pip.

### Converter Version

Managed through GitHub Releases.

Example:

```text
1.0.0
1.1.0
1.2.0
```

Automatically checked whenever the consumer executes `prime-tool-v3 run`.

Updating the converter does not require publishing a new CLI package.

### Release Structure

Each GitHub Release represents one consistent converter version.

```text
GitHub Releases
│
├── v1.0.0
│   ├── converter.py
│   ├── requirements.txt
│   └── checksums.txt
│
├── v1.1.0
│   ├── converter.py
│   ├── requirements.txt
│   └── checksums.txt
│
└── v1.2.0
    ├── converter.py
    ├── requirements.txt
    └── checksums.txt
```

The CLI downloads the assets associated with a specific release rather than retrieving individual files from the repository's latest commit.

This ensures that the converter script and its dependency manifest belong to the same release.

## Local Storage

PrimeToolv3 maintains its own application directory.

### Linux / macOS

```text
~/.primetoolv3/
│
├── script/
│   └── converter.py
│
├── venv/
│   └── ...
│
├── metadata/
│   └── version.json
│
└── logs/
```

### Windows

```text
%LOCALAPPDATA%\primetoolv3\
│
├── script/
│   └── converter.py
│
├── venv/
│   └── ...
│
├── metadata/
│   └── version.json
│
└── logs/
```

All converter-related resources are contained within this directory.

The CLI package itself remains installed in the consumer's existing Python environment.

## Project Structure

The entire project is maintained in a single GitHub repository.

```text
prime-tool-v3/
│
├── .github/
│   └── workflows/
│       └── publish.yml
│
├── src/
│   └── primetoolv3/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       │
│       ├── core/
│       │   ├── downloader.py
│       │   ├── version_manager.py
│       │   ├── environment.py
│       │   ├── dependency_manager.py
│       │   └── executor.py
│       │
│       └── utils/
│           ├── paths.py
│           ├── platform.py
│           └── logger.py
│
├── engine/
│   ├── tool.py
│   ├── requirements.txt
│   └── version.txt
│
├── pyproject.toml
├── README.md
└── LICENSE
```

### Directory Responsibilities

| Directory / File | Purpose |
|---|---|
| `src/prime-tool-v3/` | CLI package implementation |
| `src/prime-tool-v3/core/` | Core application logic |
| `src/prime-tool-v3/utils/` | Shared utilities |
| `engine/` | Actual converter source and dependency manifest |
| `.github/workflows/` | Automated release and publishing workflows |
| `pyproject.toml` | Python package configuration |
| `README.md` | Project documentation |
| `LICENSE` | Project licensing |

Only the CLI package is distributed through PyPI.

The `engine/` directory is maintained in GitHub and distributed separately through GitHub Releases.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| CLI argument parsing | argparse |
| Package configuration | pyproject.toml |
| CLI distribution | PyPI |
| Source control | GitHub |
| Converter distribution | GitHub Releases |
| Remote communication | HTTPS |
| Environment management | Python venv |
| Dependency installation | pip |
| Local metadata | JSON |
| Versioning | Semantic Versioning |

## Security

Security is an important consideration because the CLI downloads and executes remote Python code.

The implementation follows these principles:

- All downloads use HTTPS.
- Downloaded assets are validated using checksums.
- Incomplete or corrupted downloads are never executed.
- Cached files are replaced atomically.
- Converter dependencies are installed only inside the dedicated virtual environment.
- Dependency installation requires explicit user confirmation.
- Private credentials are never embedded in the converter or CLI.
- Release assets are associated with specific versioned releases.
- The converter source remains publicly inspectable.

PrimeToolV3 executes publicly distributed Python code. Consumers should only use releases from the official project repository.

## Development Roadmap

Development is divided into five phases.

### Phase 1: CLI Foundation

- [ ] Create the Python package.
- [ ] Configure `pyproject.toml`.
- [ ] Register the `prime-tool-v3` terminal command.
- [ ] Implement argument parsing.
- [ ] Implement `run`, `update`, `version` and `clean`.
- [ ] Test local package installation.

### Phase 2: GitHub Integration

- [ ] Configure the official repository URL.
- [ ] Implement GitHub release discovery.
- [ ] Implement release asset downloading.
- [ ] Implement checksum validation.
- [ ] Implement local script caching.
- [ ] Implement converter version checking.
- [ ] Implement offline fallback.

### Phase 3: Environment Management

- [ ] Implement platform-specific storage paths.
- [ ] Detect compatible Python interpreters.
- [ ] Automatically create the dedicated virtual environment.
- [ ] Implement dependency detection.
- [ ] Implement the dependency installation prompt.
- [ ] Install dependencies exclusively inside the converter environment.

### Phase 4: Execution

- [ ] Implement converter execution.
- [ ] Preserve interactive terminal input and output.
- [ ] Propagate converter exit codes.
- [ ] Implement error handling.
- [ ] Test across Linux, macOS and Windows.

### Phase 5: Publishing

- [ ] Build the PyPI distribution.
- [ ] Configure automated PyPI publishing.
- [ ] Configure GitHub Release automation.
- [ ] Publish the initial CLI package.
- [ ] Publish the initial converter release.
- [ ] Test installation and execution from a fresh consumer environment.

## Contributing

Contributions, bug reports and suggestions are welcome.

Development guidelines and contribution instructions will be added as the project matures.

## License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for details.
