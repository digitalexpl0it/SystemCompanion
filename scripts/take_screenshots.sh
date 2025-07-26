#!/bin/bash

# System Companion Screenshot Tool
# This script helps take screenshots of the application for documentation

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}📸 System Companion Screenshot Tool${NC}"
echo "======================================"

# Check if screenshots directory exists
if [ ! -d "screenshots" ]; then
    echo -e "${YELLOW}📁 Creating screenshots directory...${NC}"
    mkdir -p screenshots
fi

# Check if application is running
if ! pgrep -f "python3.*run.py" > /dev/null; then
    echo -e "${YELLOW}🚀 Starting System Companion...${NC}"
    echo -e "${BLUE}📋 Please wait for the application to start, then:${NC}"
    echo "1. Navigate to each tab you want to screenshot"
    echo "2. Press Enter when ready to take a screenshot"
    echo "3. Use Alt+PrtScn to capture the active window"
    echo "4. Save screenshots to the screenshots/ folder"
    echo ""
    
    # Start the application in background
    python3 run.py &
    APP_PID=$!
    
    echo -e "${GREEN}✅ Application started (PID: $APP_PID)${NC}"
    echo -e "${YELLOW}⏳ Waiting 5 seconds for application to load...${NC}"
    sleep 5
else
    echo -e "${GREEN}✅ System Companion is already running${NC}"
fi

# Screenshot checklist
echo ""
echo -e "${BLUE}📋 Screenshot Checklist:${NC}"
echo "================================"

SCREENSHOTS=(
    "dashboard.png:Main Dashboard (Health tab)"
    "performance.png:Performance Monitoring tab"
    "maintenance.png:System Maintenance tab"
    "security.png:Security Monitoring tab"
    "settings.png:Settings Configuration tab"
    "health-details.png:Detailed Health Monitoring"
    "benchmark-results.png:Performance Benchmark Results"
    "maintenance-tasks.png:Maintenance Task Management"
    "security-scan.png:Security Vulnerability Scan"
)

for screenshot in "${SCREENSHOTS[@]}"; do
    filename="${screenshot%%:*}"
    description="${screenshot##*:}"
    
    if [ -f "screenshots/$filename" ]; then
        echo -e "${GREEN}✅ $filename - $description${NC}"
    else
        echo -e "${YELLOW}⏳ $filename - $description${NC}"
    fi
done

echo ""
echo -e "${BLUE}📝 Screenshot Instructions:${NC}"
echo "================================"
echo "1. Navigate to each tab in System Companion"
echo "2. Use Alt+PrtScn to capture the active window"
echo "3. Save screenshots to the screenshots/ folder"
echo "4. Use the exact filenames listed above"
echo ""
echo -e "${BLUE}🛠️  Screenshot Tools:${NC}"
echo "====================="
echo "• Built-in: Alt+PrtScn (capture active window)"
echo "• GNOME Screenshot: gnome-screenshot -w"
echo "• Flameshot: flameshot gui (recommended)"
echo "• Spectacle: spectacle -b (KDE)"
echo ""

# Check for screenshot tools
if command -v flameshot &> /dev/null; then
    echo -e "${GREEN}✅ Flameshot is available${NC}"
    echo "   Run: flameshot gui"
elif command -v gnome-screenshot &> /dev/null; then
    echo -e "${GREEN}✅ GNOME Screenshot is available${NC}"
    echo "   Run: gnome-screenshot -w"
else
    echo -e "${YELLOW}⚠️  No screenshot tools detected${NC}"
    echo "   Install: sudo apt install flameshot"
fi

echo ""
echo -e "${BLUE}🎯 Tips for Professional Screenshots:${NC}"
echo "=========================================="
echo "• Use a clean, minimal desktop background"
echo "• Ensure the application window is properly sized"
echo "• Show realistic but non-sensitive system data"
echo "• Use consistent theme/colors across screenshots"
echo "• Keep file sizes under 2MB for GitHub"
echo "• Use PNG format for best quality"
echo ""

# Wait for user input
read -p "Press Enter when you're ready to start taking screenshots..."

echo -e "${GREEN}🎉 Ready to take screenshots!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Take screenshots of each tab/feature"
echo "2. Save them to the screenshots/ folder"
echo "3. Use the exact filenames from the checklist"
echo "4. Update the main README.md with your screenshots"
echo ""

# Keep the script running
echo -e "${YELLOW}💡 The application will continue running${NC}"
echo "   Close it manually when you're done taking screenshots"
echo "   Or press Ctrl+C to stop this script"

# Wait for user to finish
read -p "Press Enter when you're done taking screenshots..."

echo -e "${GREEN}✅ Screenshot session completed!${NC}"
echo ""
echo -e "${BLUE}📁 Check your screenshots in: screenshots/${NC}"
echo -e "${BLUE}📝 Update README.md with your new screenshots${NC}" 