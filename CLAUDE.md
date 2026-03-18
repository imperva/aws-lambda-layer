# CLAUDE.md - AWS Lambda Layer Project Guide

This file contains guidelines for Claude Code when working on this project.

## Project Overview

This is a Python tool that automates creation and publication of AWS Lambda layers for Python packages. The primary use case is packaging machine learning libraries (scikit-learn, xgboost) and other heavy dependencies for use in AWS Lambda functions.

- **Main Script**: `src/create_layer.py`
- **Language**: Python 3.8+
- **Key Dependencies**: Docker, boto3
- **Tests**: pytest in `test/` directory

## Architecture

### Core Components

1. **Layer Builder** (`src/create_layer.py`)
   - CLI tool for building Lambda layers using Docker
   - Supports multiple Python runtimes (3.8-3.13) and architectures (x86_64, arm64)
   - Analyzes layer size and provides optimization insights

2. **Docker Build** (`src/create_layer.Dockerfile`)
   - Multi-stage build using official AWS Lambda base images
   - Installs packages and runs cleanup scripts
   - Creates zip file compatible with Lambda layers

3. **Layer Configurations** (`layers/{name}/`)
   - Each layer has: `requirements.txt` and `cleanup.sh`
   - Currently supported: sklearn, xgboost, jinja, sqlite_utils, fastparquet
   - Extensible for new layers

4. **Tests** (`test/`)
   - Unit tests: `create_layer_unit.py`
   - Integration tests: `create_layer_test.py`

## Key Workflows

### Adding a New Layer

1. Create `layers/{package_name}/` directory
2. Add `requirements.txt` with pip packages
3. Add `cleanup.sh` to remove unnecessary files
4. Test: `python src/create_layer.py -l {package_name}`

### Building a Layer

Command structure:
```bash
python src/create_layer.py -l {layer} [-r runtime] [-a architecture] [-p publish] [--bucket s3_bucket]
```

- `-l`: Layer name (required)
- `-r`: Python runtime, default "3.13"
- `-a`: Architecture, default "x86_64" (or "arm64")
- `-p`: Publish to Lambda (true/false)
- `--bucket`: S3 bucket for publishing
- `-t`: Top N items to show in analysis (default 10)

### Output

- Layer zip files go to `outputs/` directory
- Named format: `{layer}_{runtime}_{architecture}.zip`
- Tool reports layer size and largest files/directories/types

## Code Quality Standards

- **Type hints**: Use where helpful but not required for simple functions
- **Error handling**: Catch Docker exceptions gracefully, provide clear error messages
- **Logging**: Use Python logging module (configured in `logging.conf`)
- **Testing**: Unit tests for utility functions (platform detection, size formatting)
- **Cleanup**: Remove test files/documentation to keep layers minimal

## Development Environment

### Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r test/test.requirements.txt
```

### Run Tests
```bash
PYTHONPATH=src:test python -m pytest --color=yes test/*_unit.py
```

### Dependencies
- `docker` - For building layers
- `boto3` - For AWS Lambda/S3 operations
- `pytest` - For testing

## Important Notes

1. **Docker Required**: The tool uses Docker to build layers. Docker daemon must be running.
2. **AWS Credentials**: Only needed when publishing layers (using `-p true --bucket`)
3. **Memory & Time**: Layer building is I/O intensive. ML packages (sklearn) take 5-10 minutes.
4. **Platform Selection**: Architecture must match target Lambda (x86_64 is most common, arm64 for Graviton)
5. **Python Runtime**: Must match the Lambda runtime where the layer will be used

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Docker not running | Start Docker daemon before running the script |
| Layer too large | Review `cleanup.sh`, consider removing test files or docs |
| Import errors in Lambda | Ensure Python runtime matches between layer build and Lambda function |
| arm64 layer on x86_64 Lambda | Rebuild with `-a x86_64` or update Lambda to use Graviton |

## File Locations

- Main script: `src/create_layer.py`
- Docker template: `src/create_layer.Dockerfile`
- Logging config: `src/logging.conf`
- Unit tests: `test/create_layer_unit.py`
- Integration tests: `test/create_layer_test.py`
- Layer configs: `layers/{name}/requirements.txt` and `cleanup.sh`
- Built layers: `outputs/*.zip`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Code style
- Testing requirements
- Pull request process
- License agreement

## Related Documentation

- AWS Lambda Layer Concepts: https://docs.aws.amazon.com/lambda/latest/dg/chapter-layers.html
- AWS Lambda Python Runtimes: https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html
- Project README: [README.md](README.md)
