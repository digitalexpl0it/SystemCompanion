#!/bin/bash
# System Companion - Development Environment Setup Script
# This script sets up a fresh Ubuntu system for System Companion development

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a package is installed
package_installed() {
    dpkg -l "$1" >/dev/null 2>&1
}

print_status "Starting System Companion development environment setup..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Please run as a regular user."
   exit 1
fi

# Update package list
print_status "Updating package list..."
sudo apt update

# Check and install Python
print_status "Checking Python installation..."
if ! command_exists python3; then
    print_warning "Python 3 not found. Installing..."
    sudo apt install -y python3 python3-pip python3-venv
else
    PYTHON_VERSION=$(python3 --version)
    print_success "Python found: $PYTHON_VERSION"
fi

# Check Python version
PYTHON_VERSION_NUM=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$PYTHON_VERSION_NUM >= 3.11" | bc -l) -eq 0 ]]; then
    print_error "Python 3.11 or higher is required. Current version: $PYTHON_VERSION_NUM"
    print_status "Please upgrade Python or use pyenv to install a newer version."
    exit 1
fi

# Check and install build tools
print_status "Checking build tools..."

# Meson
if ! command_exists meson; then
    print_warning "Meson not found. Installing..."
    sudo apt install -y meson
else
    MESON_VERSION=$(meson --version)
    print_success "Meson found: $MESON_VERSION"
fi

# Ninja
if ! command_exists ninja; then
    print_warning "Ninja not found. Installing..."
    sudo apt install -y ninja-build
else
    NINJA_VERSION=$(ninja --version)
    print_success "Ninja found: $NINJA_VERSION"
fi

# Check and install GTK4 development libraries
print_status "Checking GTK4 development libraries..."

GTK4_PACKAGES=(
    "libgtk-4-dev"
    "libadwaita-1-dev"
    "python3-gi"
    "python3-gi-cairo"
    "gir1.2-gtk-4.0"
    "gir1.2-adw-1"
)

for package in "${GTK4_PACKAGES[@]}"; do
    if ! package_installed "$package"; then
        print_warning "$package not found. Installing..."
        sudo apt install -y "$package"
    else
        print_success "$package is already installed"
    fi
done

# Check and install additional development tools
print_status "Checking additional development tools..."

DEV_TOOLS=(
    "git"
    "build-essential"
    "pkg-config"
    "libcairo2-dev"
    "libpango1.0-dev"
    "libgirepository1.0-dev"
)

for tool in "${DEV_TOOLS[@]}"; do
    if ! package_installed "$tool"; then
        print_warning "$tool not found. Installing..."
        sudo apt install -y "$tool"
    else
        print_success "$tool is already installed"
    fi
done

# Create virtual environment
print_status "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment and install Python dependencies
print_status "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install development dependencies
print_status "Installing development dependencies..."
pip install -e .[dev]

# Test GTK4 installation
print_status "Testing GTK4 installation..."
python3 -c "
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1.0')
from gi.repository import Gtk, Adw
print('GTK4 and libadwaita are working correctly!')
"

if [ $? -eq 0 ]; then
    print_success "GTK4 and libadwaita are properly installed"
else
    print_error "GTK4 installation test failed"
    exit 1
fi

# Test build system
print_status "Testing build system..."
if [ -d "build" ]; then
    rm -rf build
fi

meson setup build
cd build
ninja

if [ $? -eq 0 ]; then
    print_success "Build system is working correctly"
else
    print_error "Build system test failed"
    exit 1
fi

cd ..

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p ~/.config/system-companion
mkdir -p ~/.local/share/system-companion/logs
mkdir -p ~/.cache/system-companion

print_success "Development environment setup completed successfully!"
print_status ""
print_status "Next steps:"
print_status "1. Activate the virtual environment: source venv/bin/activate"
print_status "2. Run the application: python3 src/system_companion/main.py"
print_status "3. Run tests: pytest tests/"
print_status "4. Build the project: meson setup build && cd build && ninja"
print_status ""
print_status "Happy coding! 🚀" 