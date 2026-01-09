# Artifactiq Releases

Public releases for Artifactiq Core - the high-performance AI-powered visual intelligence engine.

## Downloads

See [Releases](https://github.com/ARTIFACTIQ/releases/releases) for the latest binaries.

### Available Platforms

| Platform | Architecture | File |
|----------|-------------|------|
| Linux | x86_64 | `artifactiq-linux-amd64.tar.gz` |
| macOS | Intel (x86_64) | `artifactiq-darwin-amd64.tar.gz` |
| macOS | Apple Silicon (arm64) | `artifactiq-darwin-arm64.tar.gz` |

### Installation

```bash
# Download using gh CLI (recommended)
gh release download --repo ARTIFACTIQ/releases --pattern "*arm64*"

# Or using curl
curl -LO https://github.com/ARTIFACTIQ/releases/releases/latest/download/artifactiq-darwin-arm64.tar.gz
curl -LO https://github.com/ARTIFACTIQ/releases/releases/latest/download/artifactiq-darwin-arm64.tar.gz.sha256

# Verify checksum
shasum -a 256 -c artifactiq-darwin-arm64.tar.gz.sha256

# Extract and run
tar xzf artifactiq-darwin-arm64.tar.gz
./artifactiq --help
```

### Verification

All releases include SHA256 checksums (`.sha256` files) for verification.

```bash
# Verify integrity
shasum -a 256 -c <filename>.sha256
```

## Source Code

The source code is maintained in a private repository. For licensing inquiries, contact [dev@artifactiq.ai](mailto:dev@artifactiq.ai).
