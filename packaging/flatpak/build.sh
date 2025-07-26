#!/bin/bash

# System Companion Flatpak Build Script
# This script builds the Flatpak package for System Companion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_ID="org.systemcompanion.app"
MANIFEST_FILE="org.systemcompanion.app.yml"
BUILD_DIR="build-dir"
REPO_DIR="repo"

echo -e "${BLUE}🚀 System Companion Flatpak Builder${NC}"
echo "=================================="

# Check if flatpak-builder is installed
if ! command -v flatpak-builder &> /dev/null; then
    echo -e "${RED}❌ flatpak-builder is not installed${NC}"
    echo "Please install it with: sudo apt install flatpak-builder"
    exit 1
fi

# Check if required runtimes are installed
echo -e "${YELLOW}📦 Checking Flatpak runtimes...${NC}"
if ! flatpak list | grep -q "org.gnome.Platform"; then
    echo -e "${YELLOW}⚠️  Installing GNOME Platform runtime...${NC}"
    flatpak install org.gnome.Platform//45 -y
fi

if ! flatpak list | grep -q "org.gnome.Sdk"; then
    echo -e "${YELLOW}⚠️  Installing GNOME SDK...${NC}"
    flatpak install org.gnome.Sdk//45 -y
fi

# Clean previous builds
echo -e "${YELLOW}🧹 Cleaning previous builds...${NC}"
rm -rf "$BUILD_DIR" "$REPO_DIR"

# Build the Flatpak
echo -e "${BLUE}🔨 Building Flatpak package...${NC}"
flatpak-builder \
    --force-clean \
    --repo="$REPO_DIR" \
    "$BUILD_DIR" \
    "$MANIFEST_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Flatpak build completed successfully!${NC}"
else
    echo -e "${RED}❌ Flatpak build failed${NC}"
    exit 1
fi

# Create a bundle (optional)
echo -e "${BLUE}📦 Creating Flatpak bundle...${NC}"
flatpak build-bundle "$REPO_DIR" "system-companion-0.1.0.flatpak" "$APP_ID"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Flatpak bundle created: system-companion-0.1.0.flatpak${NC}"
else
    echo -e "${YELLOW}⚠️  Bundle creation failed, but build was successful${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Build completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Install the app: flatpak install --user system-companion-0.1.0.flatpak"
echo "2. Run the app: flatpak run $APP_ID"
echo "3. Or install from repo: flatpak install --user --sideload-repo=$REPO_DIR $APP_ID"
echo ""
echo -e "${BLUE}📁 Build artifacts:${NC}"
echo "- Build directory: $BUILD_DIR"
echo "- Repository: $REPO_DIR"
echo "- Bundle: system-companion-0.1.0.flatpak" 