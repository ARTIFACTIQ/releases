# Artifactiq Releases

Public releases for Artifactiq Core - the high-performance AI-powered visual intelligence engine.

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
curl -LO https://github.com/ARTIFACTIQ/releases/releases/latest/download/artifactiq-darwin-arm64.tar.gz.sha256

# Or Linux x86_64
curl -LO https://github.com/ARTIFACTIQ/releases/releases/latest/download/artifactiq-linux-amd64.tar.gz
curl -LO https://github.com/ARTIFACTIQ/releases/releases/latest/download/artifactiq-linux-amd64.tar.gz.sha256

# Verify checksum
shasum -a 256 -c *.sha256

# Extract and run
tar xzf artifactiq-*.tar.gz
./artifactiq --help
```

## Getting Started

```bash
# Show version and feature info
artifactiq info

# List available models
artifactiq models

# Download a detection model
artifactiq download --model yolov8n

# Analyze an image
artifactiq analyze --input image.jpg --model yolov8n
```

### Model Management

Artifactiq integrates with [mlOS Axon](https://github.com/mlOS-foundation/axon) for model management. If Axon is installed, models are automatically managed through it.

```bash
# With Axon installed
axon install hf/ultralytics/yolov8n
artifactiq analyze --input image.jpg --model yolov8n

# Without Axon - direct download
artifactiq download --model yolov8n
```

## Verification

All releases include SHA256 checksums (`.sha256` files) for verification.

```bash
# Verify integrity
shasum -a 256 -c <filename>.sha256
```

## Source Code

The source code is maintained in a private repository. For licensing inquiries, contact [dev@artifactiq.ai](mailto:dev@artifactiq.ai).
