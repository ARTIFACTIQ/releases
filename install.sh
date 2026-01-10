#!/bin/sh
set -e

# Artifactiq Installer
# Works on Linux (x64) and macOS (ARM64)
#
# Usage:
#   curl -fsSL https://artifactiq.ai/install.sh | sh
#
# Environment variables:
#   ARTIFACTIQ_VERSION     - Specific version to install (default: latest)
#   ARTIFACTIQ_INSTALL_DIR - Installation directory (default: ~/.local/bin)

VERSION="${ARTIFACTIQ_VERSION:-latest}"
INSTALL_DIR="${ARTIFACTIQ_INSTALL_DIR:-$HOME/.local/bin}"

# Colors (only if terminal supports it)
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    NC='\033[0m'
else
    GREEN=''
    BLUE=''
    YELLOW=''
    RED=''
    NC=''
fi

info() {
    printf "${BLUE}==>${NC} %s\n" "$1"
}

success() {
    printf "${GREEN}==>${NC} %s\n" "$1"
}

warn() {
    printf "${YELLOW}Warning:${NC} %s\n" "$1"
}

error() {
    printf "${RED}Error:${NC} %s\n" "$1" >&2
    exit 1
}

# Detect platform
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
    Linux)
        case "$ARCH" in
            x86_64) PLATFORM="linux-amd64" ;;
            *)      error "Unsupported Linux architecture: $ARCH (only x86_64 supported)" ;;
        esac
        ;;
    Darwin)
        case "$ARCH" in
            arm64) PLATFORM="darwin-arm64" ;;
            *)     error "Unsupported macOS architecture: $ARCH (only Apple Silicon supported)" ;;
        esac
        ;;
    *)
        error "Unsupported operating system: $OS"
        ;;
esac

# Get latest version if not specified
if [ "$VERSION" = "latest" ]; then
    info "Fetching latest version..."
    # Use releases list (not /latest) to include prereleases
    VERSION=$(curl -sL https://api.github.com/repos/ARTIFACTIQ/releases/releases | grep '"tag_name"' | head -1 | cut -d'"' -f4)
    if [ -z "$VERSION" ]; then
        error "Failed to fetch latest version. Check your internet connection."
    fi
fi

echo ""
echo "  ${BLUE}Artifactiq Installer${NC}"
echo "  ===================="
echo ""
info "Version:  $VERSION"
info "Platform: $PLATFORM"
info "Install:  $INSTALL_DIR"
echo ""

# Create install directory
mkdir -p "$INSTALL_DIR"

# Download URL
DOWNLOAD_URL="https://github.com/ARTIFACTIQ/releases/releases/download/${VERSION}/artifactiq-${PLATFORM}.tar.gz"

info "Downloading from GitHub..."
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

if ! curl -fsSL "$DOWNLOAD_URL" -o "$TEMP_DIR/artifactiq.tar.gz"; then
    error "Failed to download $DOWNLOAD_URL"
fi

# Download checksum
CHECKSUM_URL="${DOWNLOAD_URL}.sha256"
if curl -fsSL "$CHECKSUM_URL" -o "$TEMP_DIR/checksum.sha256" 2>/dev/null; then
    info "Verifying checksum..."
    cd "$TEMP_DIR"
    # Fix checksum file to use local filename
    EXPECTED_HASH=$(cat checksum.sha256 | awk '{print $1}')
    ACTUAL_HASH=$(shasum -a 256 artifactiq.tar.gz | awk '{print $1}')
    if [ "$EXPECTED_HASH" != "$ACTUAL_HASH" ]; then
        error "Checksum verification failed!"
    fi
    success "Checksum verified"
    cd - > /dev/null
else
    warn "Checksum file not available, skipping verification"
fi

# Extract
info "Extracting..."
tar xzf "$TEMP_DIR/artifactiq.tar.gz" -C "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/artifactiq"

echo ""
success "Artifactiq installed successfully!"
echo ""
echo "  Binary location: $INSTALL_DIR/artifactiq"
echo ""

# Check if in PATH
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$INSTALL_DIR"; then
    echo "  ${YELLOW}Add to your PATH:${NC}"
    echo ""
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "  Add this line to your ~/.bashrc, ~/.zshrc, or ~/.profile"
    echo ""
fi

echo "  ${BLUE}Get started:${NC}"
echo ""
echo "    artifactiq --help"
echo "    artifactiq info"
echo "    artifactiq models"
echo ""
