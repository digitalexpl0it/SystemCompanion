#!/bin/bash

# System Companion AppImage Builder
# This script builds an AppImage package for System Companion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="System_Companion"
APP_VERSION="0.1.0"
SOURCE_APP_DIR="AppDir"
BUILD_APP_DIR="build/AppDir"
BUILD_DIR="build"
DIST_DIR="dist"

echo -e "${BLUE}🚀 System Companion AppImage Builder${NC}"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "$SOURCE_APP_DIR/AppRun" ]; then
    echo -e "${RED}❌ AppRun file not found in $SOURCE_APP_DIR directory${NC}"
    exit 1
fi

# Create build directories
echo -e "${YELLOW}📁 Creating build directories...${NC}"
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Check if appimagetool is available
if ! command -v appimagetool &> /dev/null; then
    echo -e "${YELLOW}📦 Installing appimagetool...${NC}"
    
    # Check if appimagetool exists in current directory
    if [ -f "./appimagetool" ]; then
        echo -e "${GREEN}✅ Using existing appimagetool${NC}"
        chmod +x ./appimagetool
        export PATH="$PWD:$PATH"
    else
        # Download appimagetool
        wget -O appimagetool "https://github.com/AppImage/AppImageKit/releases/download/12/appimagetool-x86_64.AppImage"
        chmod +x appimagetool
        export PATH="$PWD:$PATH"
    fi
fi

# Create AppDir structure
echo -e "${YELLOW}🏗️  Creating AppDir structure...${NC}"
rm -rf "$BUILD_APP_DIR"
mkdir -p "$BUILD_APP_DIR/usr/bin"
mkdir -p "$BUILD_APP_DIR/usr/lib/python3.11/site-packages"
mkdir -p "$BUILD_APP_DIR/usr/share/applications"
mkdir -p "$BUILD_APP_DIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$BUILD_APP_DIR/usr/share/system-companion/css"
mkdir -p "$BUILD_APP_DIR/etc/xdg"

# Copy application files
echo -e "${BLUE}📋 Copying application files...${NC}"

# Copy Python application
cp -r ../../src/system_companion "$BUILD_APP_DIR/usr/lib/python3.11/site-packages/"

# Copy launcher script
cp ../../run.py "$BUILD_APP_DIR/usr/bin/system-companion"
chmod +x "$BUILD_APP_DIR/usr/bin/system-companion"

# Copy desktop file
cp "$SOURCE_APP_DIR/system-companion.desktop" "$BUILD_APP_DIR/usr/share/applications/"
cp "$SOURCE_APP_DIR/system-companion.desktop" "$BUILD_APP_DIR/"

# Copy icon
cp ../../resources/icons/scalable/apps/system-companion.svg "$BUILD_APP_DIR/usr/share/icons/hicolor/scalable/apps/"
cp ../../resources/icons/256x256/apps/system-companion.png "$BUILD_APP_DIR/system-companion.png"

# Copy CSS
cp ../../resources/css/style.css "$BUILD_APP_DIR/usr/share/system-companion/css/"

# Copy AppRun
cp "$SOURCE_APP_DIR/AppRun" "$BUILD_APP_DIR/"
chmod +x "$BUILD_APP_DIR/AppRun"

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"

# Create a temporary virtual environment for dependency installation
python3 -m venv temp_venv
source temp_venv/bin/activate

# Install dependencies
pip install --target="$BUILD_APP_DIR/usr/lib/python3.11/site-packages" \
    psutil>=5.9.0 \
    py-cpuinfo>=9.0.0 \
    GPUtil>=1.4.0 \
    netifaces>=0.11.0

# Deactivate virtual environment
deactivate
rm -rf temp_venv

# Copy system Python libraries (GTK4 bindings)
echo -e "${BLUE}🔧 Copying system libraries...${NC}"

# Copy GTK4 and related libraries
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
DIST_PACKAGES="/usr/lib/python3/dist-packages"
echo "Found site-packages: $SITE_PACKAGES"
echo "Found dist-packages: $DIST_PACKAGES"

# Copy GTK4 bindings if they exist
for pkg in gi GLib GObject Gtk Adw; do
    # Try site-packages first
    if [ -d "$SITE_PACKAGES/$pkg" ]; then
        echo "Copying $pkg from site-packages..."
        cp -r "$SITE_PACKAGES/$pkg" "$BUILD_APP_DIR/usr/lib/python3.11/site-packages/" 2>/dev/null || true
    # Try dist-packages if not found in site-packages
    elif [ -d "$DIST_PACKAGES/$pkg" ]; then
        echo "Copying $pkg from dist-packages..."
        cp -r "$DIST_PACKAGES/$pkg" "$BUILD_APP_DIR/usr/lib/python3.11/site-packages/" 2>/dev/null || true
    else
        echo "Package $pkg not found in either location"
    fi
done

# Copy shared libraries
echo -e "${BLUE}📚 Copying shared libraries...${NC}"

# Function to copy library and its dependencies
copy_library() {
    local lib="$1"
    if [ -f "$lib" ]; then
        local libname=$(basename "$lib")
        cp "$lib" "$BUILD_APP_DIR/usr/lib/"
        echo "Copied: $libname"
    fi
}

# Copy common GTK4 libraries
mkdir -p "$BUILD_APP_DIR/usr/lib"
for lib in /usr/lib/x86_64-linux-gnu/libgtk-4-1.so* \
           /usr/lib/x86_64-linux-gnu/libgdk-4-1.so* \
           /usr/lib/x86_64-linux-gnu/libadwaita-1.so* \
           /usr/lib/x86_64-linux-gnu/libgirepository-1.0.so* \
           /usr/lib/x86_64-linux-gnu/libglib-2.0.so* \
           /usr/lib/x86_64-linux-gnu/libgobject-2.0.so* \
           /usr/lib/x86_64-linux-gnu/libcairo.so* \
           /usr/lib/x86_64-linux-gnu/libpango-1.0.so* \
           /usr/lib/x86_64-linux-gnu/libpangocairo-1.0.so*; do
    copy_library "$lib"
done

# Create AppImage
echo -e "${BLUE}📦 Creating AppImage...${NC}"
appimagetool "$BUILD_APP_DIR" "$DIST_DIR/${APP_NAME}-${APP_VERSION}-x86_64.AppImage"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ AppImage created successfully!${NC}"
    echo -e "${GREEN}📁 Location: $DIST_DIR/${APP_NAME}-${APP_VERSION}-x86_64.AppImage${NC}"
else
    echo -e "${RED}❌ AppImage creation failed${NC}"
    exit 1
fi

# Clean up
echo -e "${YELLOW}🧹 Cleaning up...${NC}"
rm -rf "$BUILD_APP_DIR"

echo ""
echo -e "${GREEN}🎉 AppImage build completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Make the AppImage executable: chmod +x $DIST_DIR/${APP_NAME}-${APP_VERSION}-x86_64.AppImage"
echo "2. Run the AppImage: ./$DIST_DIR/${APP_NAME}-${APP_VERSION}-x86_64.AppImage"
echo "3. Test the application functionality"
echo ""
echo -e "${BLUE}📁 Build artifacts:${NC}"
echo "- AppImage: $DIST_DIR/${APP_NAME}-${APP_VERSION}-x86_64.AppImage" 