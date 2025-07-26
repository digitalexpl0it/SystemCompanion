#!/bin/bash

# System Companion Icon Converter
# This script converts a PNG icon to SVG and generates all required sizes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎨 System Companion Icon Converter${NC}"
echo "======================================"

# Check if input file is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Please provide the path to your PNG icon${NC}"
    echo "Usage: $0 /path/to/your/icon.png"
    echo ""
    echo -e "${BLUE}Example:${NC}"
    echo "  $0 ~/Downloads/my-icon.png"
    echo "  $0 ./icon.png"
    exit 1
fi

INPUT_FILE="$1"
ICON_NAME="system-companion"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo -e "${RED}❌ File not found: $INPUT_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found input file: $INPUT_FILE${NC}"

# Check if Inkscape is installed
if ! command -v inkscape &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Inkscape...${NC}"
    sudo apt update
    sudo apt install -y inkscape
fi

# Check if ImageMagick is installed (for PNG optimization)
if ! command -v convert &> /dev/null; then
    echo -e "${YELLOW}📦 Installing ImageMagick...${NC}"
    sudo apt update
    sudo apt install -y imagemagick
fi

# Create icon directories if they don't exist
echo -e "${YELLOW}📁 Ensuring icon directories exist...${NC}"
mkdir -p resources/icons/scalable/apps
mkdir -p resources/icons/16x16/apps
mkdir -p resources/icons/32x32/apps
mkdir -p resources/icons/48x48/apps
mkdir -p resources/icons/64x64/apps
mkdir -p resources/icons/128x128/apps
mkdir -p resources/icons/256x256/apps
mkdir -p resources/icons/512x512/apps

# Step 1: Create SVG from PNG using Inkscape
echo -e "${BLUE}🔄 Converting PNG to SVG...${NC}"
SVG_OUTPUT="resources/icons/scalable/apps/${ICON_NAME}.svg"

# Use Inkscape to trace the PNG and create SVG
inkscape --export-type=svg --export-filename="$SVG_OUTPUT" "$INPUT_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ SVG created: $SVG_OUTPUT${NC}"
else
    echo -e "${YELLOW}⚠️  SVG conversion may need manual adjustment${NC}"
    echo "You can manually edit the SVG in Inkscape for better results"
fi

# Step 2: Generate PNG versions from the SVG
echo -e "${BLUE}🔄 Generating PNG versions...${NC}"

SIZES=(16 32 48 64 128 256 512)

for size in "${SIZES[@]}"; do
    PNG_OUTPUT="resources/icons/${size}x${size}/apps/${ICON_NAME}.png"
    echo -e "${YELLOW}📏 Generating ${size}x${size} PNG...${NC}"
    
    inkscape --export-type=png --export-width=$size --export-height=$size \
        --export-filename="$PNG_OUTPUT" "$SVG_OUTPUT"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Created: $PNG_OUTPUT${NC}"
    else
        echo -e "${RED}❌ Failed to create: $PNG_OUTPUT${NC}"
    fi
done

# Step 3: Optimize PNG files
echo -e "${BLUE}🔧 Optimizing PNG files...${NC}"
for size in "${SIZES[@]}"; do
    PNG_FILE="resources/icons/${size}x${size}/apps/${ICON_NAME}.png"
    if [ -f "$PNG_FILE" ]; then
        echo -e "${YELLOW}📦 Optimizing ${size}x${size}...${NC}"
        convert "$PNG_FILE" -strip -quality 95 "$PNG_FILE"
    fi
done

# Step 4: Create a simple SVG if the conversion failed
if [ ! -f "$SVG_OUTPUT" ] || [ ! -s "$SVG_OUTPUT" ]; then
    echo -e "${YELLOW}⚠️  Creating fallback SVG...${NC}"
    cat > "$SVG_OUTPUT" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <!-- Fallback icon - replace with your actual icon -->
  <rect width="512" height="512" fill="#4a90e2" rx="64"/>
  <circle cx="256" cy="256" r="128" fill="white" opacity="0.9"/>
  <circle cx="256" cy="256" r="96" fill="#4a90e2"/>
  <circle cx="256" cy="256" r="64" fill="white"/>
  <circle cx="256" cy="256" r="32" fill="#4a90e2"/>
  <text x="256" y="480" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="48" font-weight="bold">SC</text>
</svg>
EOF
    echo -e "${GREEN}✅ Fallback SVG created${NC}"
fi

# Step 5: Test the icon
echo -e "${BLUE}🧪 Testing icon...${NC}"
if [ -f "$SVG_OUTPUT" ]; then
    echo -e "${GREEN}✅ SVG icon is ready: $SVG_OUTPUT${NC}"
    echo -e "${GREEN}✅ PNG icons are ready in resources/icons/*/apps/${ICON_NAME}.png${NC}"
else
    echo -e "${RED}❌ Icon creation failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Icon conversion completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Review the generated SVG: $SVG_OUTPUT"
echo "2. If needed, edit the SVG in Inkscape for better quality"
echo "3. Test the icon in your application"
echo "4. Update the desktop files to use the new icon"
echo ""
echo -e "${BLUE}🔧 Manual optimization tips:${NC}"
echo "- Open the SVG in Inkscape for manual adjustments"
echo "- Ensure the icon works well in both light and dark themes"
echo "- Test at different sizes to ensure readability"
echo "- Consider adding a subtle drop shadow for better visibility"
echo ""
echo -e "${BLUE}📁 Generated files:${NC}"
echo "- SVG: $SVG_OUTPUT"
for size in "${SIZES[@]}"; do
    echo "- PNG ${size}x${size}: resources/icons/${size}x${size}/apps/${ICON_NAME}.png"
done 