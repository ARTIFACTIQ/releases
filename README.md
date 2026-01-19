# Artifactiq Releases

Public releases for Artifactiq Core - the high-performance AI-powered visual intelligence engine.

## Prerequisites

**mlOS Axon v3.3.0+** is **required** for model management with YOLO ONNX support. Install it first:

```bash
curl -sSL axon.mlosfoundation.org | sh
```

Learn more at [mlosfoundation.org](https://mlosfoundation.org)

## Quick Start

### Step 1: Install Axon (Required)

```bash
curl -sSL axon.mlosfoundation.org | sh
```

### Step 2: Install Artifactiq

```bash
curl -fsSL https://artifactiq.ai/install.sh | sh
```

This automatically detects your platform and installs to `~/.local/bin`.

### Step 3: Download a Model

```bash
# Install YOLOv8 nano (fastest, 6MB) with ONNX conversion
axon install hf/ultralytics/yolov8n --format onnx
```

### Step 4: Analyze an Image

```bash
artifactiq analyze --input photo.jpg --model yolov8n
```

## Validate Your Installation

After installation, run these commands to verify everything is working:

```bash
# Check Artifactiq version
artifactiq --version
# Expected: artifactiq 1.0.0-alpha.11

# Check model backend status
artifactiq models
# Should show Axon is configured

# List installed models
axon list
# Should show yolov8n if you installed it

# Test with a sample image (download a test image first)
curl -o test.jpg https://ultralytics.com/images/bus.jpg
artifactiq analyze --input test.jpg --model yolov8n
# Should detect: bus, person, etc.
```

### Expected Output

```
Analysis Results
================

Detected 4 objects:
  - person (95.2%)
  - person (91.7%)
  - bus (89.3%)
  - person (85.1%)

Processing time: 47ms
```

## Install Options

```bash
# Install specific version
ARTIFACTIQ_VERSION=v1.0.0-alpha.11 curl -fsSL https://artifactiq.ai/install.sh | sh

# Install to custom directory
ARTIFACTIQ_INSTALL_DIR=/usr/local/bin curl -fsSL https://artifactiq.ai/install.sh | sh
```

## Available Models

Use Axon to install detection models (requires Axon v3.3.0+ for ONNX conversion):

| Model | Size | Speed | Accuracy | Install Command |
|-------|------|-------|----------|-----------------|
| yolov8n | 6 MB | Fastest | Good | `axon install hf/ultralytics/yolov8n --format onnx` |
| yolov8s | 22 MB | Fast | Better | `axon install hf/ultralytics/yolov8s --format onnx` |
| yolov8m | 52 MB | Medium | Great | `axon install hf/ultralytics/yolov8m --format onnx` |
| yolov8l | 87 MB | Slower | Excellent | `axon install hf/ultralytics/yolov8l --format onnx` |
| yolov8x | 136 MB | Slowest | Best | `axon install hf/ultralytics/yolov8x --format onnx` |

## Usage Examples

```bash
# Basic detection
artifactiq analyze --input photo.jpg --model yolov8n

# JSON output for programmatic use
artifactiq analyze --input photo.jpg --model yolov8n --format json

# Process multiple images
artifactiq analyze --input ./images/ --model yolov8n

# With merchandise detection enabled
artifactiq analyze --input photo.jpg --model yolov8n --merchandise

# Set confidence threshold
artifactiq analyze --input photo.jpg --model yolov8n --confidence 0.5
```

## CLI Reference

```bash
# Show help
artifactiq --help

# Show version and system info
artifactiq info

# List available/installed models
artifactiq models
artifactiq models --installed

# Download a model (via Axon)
artifactiq download --model yolov8n

# Analyze images
artifactiq analyze --input <path> --model <model>
```

## Downloads

See [Releases](https://github.com/ARTIFACTIQ/releases/releases) for all binaries.

### Available Platforms

| Platform | Architecture | File |
|----------|-------------|------|
| Linux | x86_64 | `artifactiq-linux-amd64.tar.gz` |
| macOS | Apple Silicon (arm64) | `artifactiq-darwin-arm64.tar.gz` |

### Manual Installation

```bash
# Download using gh CLI
gh release download --repo ARTIFACTIQ/releases --pattern "*arm64*"

# Or using curl (macOS Apple Silicon)
curl -LO https://github.com/ARTIFACTIQ/releases/releases/latest/download/artifactiq-darwin-arm64.tar.gz

# Or Linux x86_64
curl -LO https://github.com/ARTIFACTIQ/releases/releases/latest/download/artifactiq-linux-amd64.tar.gz

# Verify checksum
shasum -a 256 -c *.sha256

# Extract and install
tar xzf artifactiq-*.tar.gz
chmod +x artifactiq
sudo mv artifactiq /usr/local/bin/
```

## Model Management with Axon

[mlOS Axon](https://mlosfoundation.org) handles model downloads, caching, and format conversions.

```bash
# Search for models
axon search yolo

# Install a model with ONNX conversion
axon install hf/ultralytics/yolov8n --format onnx

# List installed models
axon list

# Get model info
axon info yolov8n

# Update models
axon update
```

## Verification

All releases include SHA256 checksums (`.sha256` files) for verification:

```bash
shasum -a 256 -c artifactiq-*.sha256
```

## Troubleshooting

### "Model not found" error

Ensure Axon v3.3.0+ is installed and the model is downloaded:
```bash
# Check Axon installation (requires v3.3.0+ for YOLO ONNX)
axon --version

# Install the model with ONNX conversion
axon install hf/ultralytics/yolov8n --format onnx

# Verify model is installed
axon list
```

### "Axon not configured" error

Install Axon first:
```bash
curl -sSL axon.mlosfoundation.org | sh
```

Then restart your terminal or run:
```bash
source ~/.bashrc  # or ~/.zshrc
```

### Permission denied

Ensure the binary is executable:
```bash
chmod +x ~/.local/bin/artifactiq
```

## Support

- **Issues**: [GitHub Issues](https://github.com/ARTIFACTIQ/releases/issues)
- **Contact**: [dev@artifactiq.ai](mailto:dev@artifactiq.ai)
- **Website**: [artifactiq.ai](https://artifactiq.ai)

## Source Code

The source code is maintained in a private repository. For licensing inquiries, contact [dev@artifactiq.ai](mailto:dev@artifactiq.ai).
