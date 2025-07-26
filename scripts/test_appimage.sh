#!/bin/bash

# System Companion AppImage Tester
# This script tests the AppImage package

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing System Companion AppImage${NC}"
echo "======================================"

# Check if AppImage exists
APPIMAGE_PATH=""
if [ -f "System_Companion-0.1.0-x86_64.AppImage" ]; then
    APPIMAGE_PATH="System_Companion-0.1.0-x86_64.AppImage"
elif [ -f "packaging/appimage/dist/System_Companion-0.1.0-x86_64.AppImage" ]; then
    APPIMAGE_PATH="packaging/appimage/dist/System_Companion-0.1.0-x86_64.AppImage"
else
    echo -e "${RED}❌ AppImage not found${NC}"
    echo "Please build the AppImage first:"
    echo "  cd packaging/appimage && ./build.sh"
    exit 1
fi

echo -e "${GREEN}✅ Found AppImage: $APPIMAGE_PATH${NC}"

# Check file size
SIZE=$(du -h "$APPIMAGE_PATH" | cut -f1)
echo -e "${BLUE}📊 AppImage size: $SIZE${NC}"

# Check if executable
if [ -x "$APPIMAGE_PATH" ]; then
    echo -e "${GREEN}✅ AppImage is executable${NC}"
else
    echo -e "${YELLOW}⚠️  Making AppImage executable...${NC}"
    chmod +x "$APPIMAGE_PATH"
fi

# Test help command
echo -e "${YELLOW}🔍 Testing help command...${NC}"
if timeout 10s "$APPIMAGE_PATH" --help > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Help command works${NC}"
else
    echo -e "${RED}❌ Help command failed${NC}"
fi

# Test application startup
echo -e "${YELLOW}🚀 Testing application startup...${NC}"
echo -e "${BLUE}📋 Starting application (will timeout after 10 seconds)...${NC}"

if timeout 10s "$APPIMAGE_PATH" > /tmp/appimage_test.log 2>&1; then
    echo -e "${GREEN}✅ Application started successfully${NC}"
else
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo -e "${GREEN}✅ Application started successfully (timeout reached)${NC}"
    else
        echo -e "${RED}❌ Application failed to start (exit code: $EXIT_CODE)${NC}"
        echo -e "${YELLOW}📋 Last 10 lines of log:${NC}"
        tail -10 /tmp/appimage_test.log
    fi
fi

# Check for common issues
echo -e "${YELLOW}🔍 Checking for common issues...${NC}"

# Check if GTK libraries are included
if strings "$APPIMAGE_PATH" | grep -q "libgtk"; then
    echo -e "${GREEN}✅ GTK libraries detected${NC}"
else
    echo -e "${YELLOW}⚠️  GTK libraries not detected${NC}"
fi

# Check if Python is accessible
if strings "$APPIMAGE_PATH" | grep -q "python"; then
    echo -e "${GREEN}✅ Python references detected${NC}"
else
    echo -e "${YELLOW}⚠️  Python references not detected${NC}"
fi

# Check if icon is included
if strings "$APPIMAGE_PATH" | grep -q "system-companion"; then
    echo -e "${GREEN}✅ Application files detected${NC}"
else
    echo -e "${YELLOW}⚠️  Application files not detected${NC}"
fi

# Test desktop integration
echo -e "${YELLOW}🖥️  Testing desktop integration...${NC}"

# Extract desktop file
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Extract AppImage to check contents
"$APPIMAGE_PATH" --appimage-extract > /dev/null 2>&1 || true

if [ -f "squashfs-root/system-companion.desktop" ]; then
    echo -e "${GREEN}✅ Desktop file found${NC}"
    
    # Check desktop file contents
    if grep -q "Name=System Companion" squashfs-root/system-companion.desktop; then
        echo -e "${GREEN}✅ Desktop file has correct name${NC}"
    else
        echo -e "${YELLOW}⚠️  Desktop file name may be incorrect${NC}"
    fi
    
    if grep -q "Exec=" squashfs-root/system-companion.desktop; then
        echo -e "${GREEN}✅ Desktop file has executable path${NC}"
    else
        echo -e "${YELLOW}⚠️  Desktop file missing executable path${NC}"
    fi
else
    echo -e "${RED}❌ Desktop file not found${NC}"
fi

# Check for icon
if [ -f "squashfs-root/system-companion.png" ]; then
    echo -e "${GREEN}✅ Icon file found${NC}"
else
    echo -e "${YELLOW}⚠️  Icon file not found${NC}"
fi

# Clean up
cd - > /dev/null
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}🎉 AppImage testing completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Test the AppImage on a different system"
echo "2. Install the AppImage: ./$APPIMAGE_PATH"
echo "3. Run the AppImage: ./$APPIMAGE_PATH"
echo "4. Share the AppImage with others"
echo ""
echo -e "${BLUE}📁 AppImage location:${NC}"
echo "  - Project root: System_Companion-0.1.0-x86_64.AppImage"
echo "  - Build directory: packaging/appimage/dist/System_Companion-0.1.0-x86_64.AppImage"
echo ""
echo -e "${BLUE}💡 Tips:${NC}"
echo "  - The AppImage is portable and can run on any Linux system"
echo "  - No installation required - just make executable and run"
echo "  - Can be shared via USB, email, or download"
echo "  - Integrates with desktop environment automatically" 