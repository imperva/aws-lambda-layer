
# AWS Lambda Layer Builder

A Python tool to create and publish AWS Lambda layers for Python packages (scikit-learn, xgboost, jinja, sqlite_utils, or custom libraries).

## Problem Statement

Popular Python libraries like scikit-learn are not included in the basic AWS Lambda runtime. Unlike pandas, there’s no official AWS-provided Lambda layer for these packages. Compatibility issues and size constraints make creating such layers complex and error-prone.

This tool automates the process and helps you:
- Build Lambda-compatible layer packages using Docker
- Support multiple architectures (x86_64, arm64) and Python runtimes
- Analyze layer size and optimize by removing unnecessary files
- Publish layers directly to AWS Lambda

## Quick Start

### Prerequisites
- Python 3.8+
- Docker (running)
- AWS credentials (for publishing layers)

### Create a Layer

Create a scikit-learn layer for x86_64 (default):
```bash
python src/create_layer.py -l sklearn
```

Create a layer for arm64 architecture:
```bash
python src/create_layer.py -l sklearn -a arm64
```

Create a layer with Python 3.11:
```bash
python src/create_layer.py -l sklearn -r 3.11
```

### Build and Publish

Build and publish to AWS Lambda:
```bash
python src/create_layer.py -l sklearn -p true --bucket="your-s3-bucket"
```

### View All Options

```bash
python src/create_layer.py -h
```

## Supported Layers

| Layer | Description |
|-------|-------------|
| `sklearn` | scikit-learn for machine learning |
| `xgboost` | XGBoost gradient boosting |
| `jinja` | Jinja2 templating engine |
| `sqlite_utils` | SQLite utilities |
| `fastparquet` | Fast Parquet file reading/writing |

## How It Works

### Layer Creation Process

1. **Docker Build**: Uses official AWS Lambda Python base images to ensure compatibility
   - Downloads and installs packages in Lambda environment
   - Supports both x86_64 and arm64 architectures via manylinux2014 platform tags

2. **Size Optimization**: Multi-stage Docker build to clean unnecessary files
   - Removes docs, tests, cache files
   - Keeps only binary artifacts needed at runtime

3. **Analysis**: Reports layer statistics
   - Total size
   - Top 10 largest directories, files, and file types
   - Helps identify optimization opportunities

4. **Publishing** (optional):
   - Uploads to S3 bucket
   - Creates AWS Lambda layer version
   - Cleans up temporary S3 objects

### Configuration Files

Each layer requires:
1. **requirements.txt** - Python package dependencies
2. **cleanup.sh** - Script to remove unnecessary files from the layer

Example: `layers/sklearn/`
- `requirements.txt` - scikit-learn and dependencies
- `cleanup.sh` - Removes test files, documentation, etc.
- `Dockerfile` - Built from template at `src/create_layer.Dockerfile`

## Using a Layer

After publishing a layer to AWS Lambda:

1. Go to AWS Lambda console → Layers
2. Find your published layer (named like `sklearn_3_13_x86_64`)
3. When creating/editing a Lambda function, attach the layer
4. The packages will be available in your Lambda function

**Note**: Heavyweight packages like scikit-learn require more memory and runtime. Adjust Lambda configuration accordingly (e.g., 512-1024 MB memory).

## Contributing

We welcome contributions! To add support for a new package:

1. Create a new folder in `layers/{package_name}/`
2. Add `requirements.txt` and `cleanup.sh`
3. Test locally with `create_layer.py -l {package_name}`
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Architecture & Technical Details

- **Python Runtime Matching**: Uses same Python version as target Lambda for compatibility
- **Multi-Architecture**: Builds for x86_64 and arm64 using platform-specific wheel files
- **Binary-Only**: Uses `--only-binary` flag to avoid source code, keeping layer size minimal
- **Docker Multi-Stage**: First stage builds, second stage optimizes and packages

## License

See [LICENSE.md](LICENSE.md)

