#!/bin/bash

# System Companion Icon Structure Creator
# This script creates the proper icon directory structure for Ubuntu 24.04

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎨 Creating Icon Directory Structure${NC}"
echo "======================================"

# Create icon directories
echo -e "${YELLOW}📁 Creating icon directories...${NC}"

# Main icon directories
mkdir -p resources/icons/scalable/apps
mkdir -p resources/icons/16x16/apps
mkdir -p resources/icons/32x32/apps
mkdir -p resources/icons/48x48/apps
mkdir -p resources/icons/64x64/apps
mkdir -p resources/icons/128x128/apps
mkdir -p resources/icons/256x256/apps
mkdir -p resources/icons/512x512/apps

# Create placeholder files
echo -e "${BLUE}📝 Creating placeholder files...${NC}"

# SVG placeholder
cat > resources/icons/scalable/apps/system-companion.svg << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <!-- Placeholder icon - replace with your actual icon -->
  <rect width="512" height="512" fill="#4a90e2" rx="64"/>
  <circle cx="256" cy="256" r="128" fill="white" opacity="0.9"/>
  <circle cx="256" cy="256" r="96" fill="#4a90e2"/>
  <circle cx="256" cy="256" r="64" fill="white"/>
  <circle cx="256" cy="256" r="32" fill="#4a90e2"/>
  <text x="256" y="480" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="48" font-weight="bold">SC</text>
</svg>
EOF

# PNG placeholders (create simple colored squares for now)
for size in 16 32 48 64 128 256 512; do
    cat > resources/icons/${size}x${size}/apps/system-companion.png << 'EOF'
# This is a placeholder - replace with actual PNG icon
# You can generate PNG icons from the SVG using:
# inkscape -w 16 -h 16 system-companion.svg -o 16x16/apps/system-companion.png
EOF
done

echo -e "${GREEN}✅ Icon directory structure created!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Generate your icon using AI tools (see README for recommendations)"
echo "2. Save the SVG as: resources/icons/scalable/apps/system-companion.svg"
echo "3. Generate PNG versions from the SVG using Inkscape:"
echo "   inkscape -w 16 -h 16 system-companion.svg -o 16x16/apps/system-companion.png"
echo "   inkscape -w 32 -h 32 system-companion.svg -o 32x32/apps/system-companion.png"
echo "   inkscape -w 48 -h 48 system-companion.svg -o 48x48/apps/system-companion.png"
echo "   inkscape -w 64 -h 64 system-companion.svg -o 64x64/apps/system-companion.png"
echo "   inkscape -w 128 -h 128 system-companion.svg -o 128x128/apps/system-companion.png"
echo "   inkscape -w 256 -h 256 system-companion.svg -o 256x256/apps/system-companion.png"
echo "   inkscape -w 512 -h 512 system-companion.svg -o 512x512/apps/system-companion.png"
echo ""
echo -e "${BLUE}🎨 AI Icon Generation Tips:${NC}"
echo "- Use Leonardo.ai for best quality"
echo "- Prompt: 'Modern flat design system monitoring dashboard icon, Ubuntu Linux style, clean minimalist design, blue and white color scheme, scalable vector graphics'"
echo "- Generate in SVG format if possible"
echo "- Test in both light and dark themes"
echo ""
echo -e "${GREEN}🎉 Icon structure ready for your custom icon!${NC}" 