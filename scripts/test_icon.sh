#!/bin/bash

# System Companion Icon Tester
# This script tests the icon in the Ubuntu system

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing System Companion Icon${NC}"
echo "================================"

# Check if icon files exist
echo -e "${YELLOW}📁 Checking icon files...${NC}"

ICON_FILES=(
    "resources/icons/scalable/apps/system-companion.svg"
    "resources/icons/16x16/apps/system-companion.png"
    "resources/icons/32x32/apps/system-companion.png"
    "resources/icons/48x48/apps/system-companion.png"
    "resources/icons/64x64/apps/system-companion.png"
    "resources/icons/128x128/apps/system-companion.png"
    "resources/icons/256x256/apps/system-companion.png"
    "resources/icons/512x512/apps/system-companion.png"
)

for file in "${ICON_FILES[@]}"; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        echo -e "${GREEN}✅ $file ($size)${NC}"
    else
        echo -e "${YELLOW}⚠️  Missing: $file${NC}"
    fi
done

# Test SVG validity
echo ""
echo -e "${YELLOW}🔍 Testing SVG validity...${NC}"
if command -v inkscape &> /dev/null; then
    if inkscape --export-type=png --export-filename=/tmp/test-icon.png resources/icons/scalable/apps/system-companion.svg 2>/dev/null; then
        echo -e "${GREEN}✅ SVG is valid and can be rendered${NC}"
        rm -f /tmp/test-icon.png
    else
        echo -e "${YELLOW}⚠️  SVG may have issues${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Inkscape not available for SVG testing${NC}"
fi

# Test icon in system (optional)
echo ""
echo -e "${YELLOW}🖥️  Testing icon in system...${NC}"
read -p "Do you want to install the icon to the system for testing? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📦 Installing icon to system...${NC}"
    
    # Copy SVG to system
    sudo cp resources/icons/scalable/apps/system-companion.svg /usr/share/icons/hicolor/scalable/apps/
    
    # Copy PNG files to system
    for size in 16 32 48 64 128 256 512; do
        sudo cp "resources/icons/${size}x${size}/apps/system-companion.png" "/usr/share/icons/hicolor/${size}x${size}/apps/"
    done
    
    # Update icon cache
    sudo gtk-update-icon-cache -f -t /usr/share/icons/hicolor
    
    echo -e "${GREEN}✅ Icon installed to system${NC}"
    echo -e "${BLUE}📋 You can now test the icon in:${NC}"
    echo "  - Application launcher"
    echo "  - File manager"
    echo "  - Desktop shortcuts"
    echo ""
    echo -e "${YELLOW}💡 To remove the icon from system:${NC}"
    echo "  sudo rm /usr/share/icons/hicolor/scalable/apps/system-companion.svg"
    echo "  sudo rm /usr/share/icons/hicolor/*/apps/system-companion.png"
    echo "  sudo gtk-update-icon-cache -f -t /usr/share/icons/hicolor"
else
    echo -e "${YELLOW}⏭️  Skipping system installation${NC}"
fi

# Test icon in application
echo ""
echo -e "${YELLOW}🚀 Testing icon in application...${NC}"
echo -e "${BLUE}📋 The icon should now be used by:${NC}"
echo "  - Application window title bar"
echo "  - Desktop entry (if created)"
echo "  - AppImage/Flatpak packages"
echo "  - System tray (if implemented)"

# Show icon information
echo ""
echo -e "${BLUE}📊 Icon Information:${NC}"
echo "  - SVG Size: $(du -h resources/icons/scalable/apps/system-companion.svg | cut -f1)"
echo "  - 256x256 PNG: $(du -h resources/icons/256x256/apps/system-companion.png | cut -f1)"
echo "  - Total icon set: $(du -ch resources/icons/*/apps/system-companion.* | tail -1 | cut -f1)"

echo ""
echo -e "${GREEN}🎉 Icon testing completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Run the application to see the icon in action"
echo "2. Check if the icon displays correctly in the title bar"
echo "3. Test the icon in different themes (light/dark)"
echo "4. Verify the icon works in AppImage and Flatpak packages" 