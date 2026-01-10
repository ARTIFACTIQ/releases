# Artifactiq Releases

Public releases for Artifactiq Core - the high-performance AI-powered visual intelligence engine.

## Prerequisites

**mlOS Axon** is required for model management:

```bash
curl -fsSL https://get.mlos.ai | sh
```

## Quick Install

**One-liner install (recommended):**

```bash
curl -fsSL https://artifactiq.ai/install.sh | sh
```

This automatically detects your platform and installs to `~/.local/bin`.

### Install Options

```bash
# Install specific version
ARTIFACTIQ_VERSION=v1.0.0-alpha.5 curl -fsSL https://artifactiq.ai/install.sh | sh

# Install to custom directory
ARTIFACTIQ_INSTALL_DIR=/usr/local/bin curl -fsSL https://artifactiq.ai/install.sh | sh
```

## Getting Started

### 1. Install a Detection Model

```bash
# Install YOLOv8 nano (fastest, 6MB)
axon install hf/ultralytics/yolov8n

# Or larger models for better accuracy
axon install hf/ultralytics/yolov8s   # 22MB, fast
axon install hf/ultralytics/yolov8m   # 52MB, balanced
```

### 2. Analyze Images

```bash
# Analyze an image
artifactiq analyze --input photo.jpg --model yolov8n

# JSON output for programmatic use
artifactiq analyze --input photo.jpg --model yolov8n --format json

# With merchandise detection enabled
artifactiq analyze --input photo.jpg --model yolov8n --merchandise
```

### 3. Check System Info

```bash
# Show version and prerequisites status
artifactiq info

# List available models
artifactiq models

# List installed models
artifactiq models --installed
```

## Example Output

```
Analysis Results
================

Detected 3 objects:
  - person (95.2%)
  - handbag (88.1%)
  - car (72.3%)

Merchandise Opportunities: 2
  - Designer Handbag: https://shop.example.com/handbag-123
  - Similar Outfit: https://shop.example.com/outfit-456

Processing time: 47ms
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

# Extract and run
tar xzf artifactiq-*.tar.gz
./artifactiq --help
```

## Model Management with Axon

[mlOS Axon](https://github.com/mlOS-foundation/axon) handles model downloads, caching, and format conversions.

```bash
# Search for models
axon search yolo

# Install a model
axon install hf/ultralytics/yolov8n

# List installed models
axon list

# Get model info
axon info yolov8n
```

### Available Detection Models

| Model | Size | Speed | Accuracy | Install Command |
|-------|------|-------|----------|-----------------|
| yolov8n | 6 MB | Fastest | Good | `axon install hf/ultralytics/yolov8n` |
| yolov8s | 22 MB | Fast | Better | `axon install hf/ultralytics/yolov8s` |
| yolov8m | 52 MB | Medium | Great | `axon install hf/ultralytics/yolov8m` |
| yolov8l | 87 MB | Slower | Excellent | `axon install hf/ultralytics/yolov8l` |
| yolov8x | 136 MB | Slowest | Best | `axon install hf/ultralytics/yolov8x` |

## Verification

All releases include SHA256 checksums (`.sha256` files) for verification.

```bash
shasum -a 256 -c <filename>.sha256
```

## Source Code

The source code is maintained in a private repository. For licensing inquiries, contact [dev@artifactiq.ai](mailto:dev@artifactiq.ai).
