#!/usr/bin/env python3
"""
System Companion - Dependency Checker

This script checks for required dependencies and provides installation instructions.
"""

import sys
import subprocess
import shutil
from pathlib import Path


def check_command(command, description):
    """Check if a command is available."""
    if shutil.which(command):
        try:
            result = subprocess.run([command, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            version = result.stdout.strip().split('\n')[0]
            print(f"✅ {description}: {version}")
            return True
        except subprocess.TimeoutExpired:
            print(f"⚠️  {description}: Found but version check timed out")
            return True
        except Exception:
            print(f"⚠️  {description}: Found but version check failed")
            return True
    else:
        print(f"❌ {description}: Not found")
        return False


def check_python_package(package, description):
    """Check if a Python package is installed."""
    try:
        __import__(package)
        print(f"✅ {description}: Installed")
        return True
    except ImportError:
        print(f"❌ {description}: Not installed")
        return False


def main():
    """Main dependency check function."""
    print("System Companion - Dependency Checker")
    print("=" * 50)
    
    missing_deps = []
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 11:
        print(f"✅ Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python: {python_version.major}.{python_version.minor}.{python_version.micro} (3.11+ required)")
        missing_deps.append("Python 3.11+")
    
    # Check build tools
    print("\nBuild Tools:")
    if not check_command("meson", "Meson"):
        missing_deps.append("meson")
    
    if not check_command("ninja", "Ninja"):
        missing_deps.append("ninja-build")
    
    # Check GTK4 development libraries
    print("\nGTK4 Development Libraries:")
    gtk4_packages = [
        ("libgtk-4-dev", "GTK4 Development"),
        ("libadwaita-1-dev", "libadwaita Development"),
        ("python3-gi", "Python GObject Introspection"),
        ("python3-gi-cairo", "Python GObject Cairo"),
        ("gir1.2-gtk-4.0", "GTK4 GObject Introspection"),
        ("gir1.2-adw-1", "libadwaita GObject Introspection")
    ]
    
    for package, description in gtk4_packages:
        try:
            result = subprocess.run(["dpkg", "-l", package], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and "ii" in result.stdout:
                print(f"✅ {description}: Installed")
            else:
                print(f"❌ {description}: Not installed")
                missing_deps.append(package)
        except FileNotFoundError:
            print(f"❌ {description}: Cannot check (dpkg not available)")
            missing_deps.append(package)
    
    # Check Python packages
    print("\nPython Packages:")
    python_packages = [
        ("psutil", "psutil"),
        ("cpuinfo", "py-cpuinfo"),
        ("GPUtil", "GPUtil"),
        ("netifaces", "netifaces")
    ]
    
    for package, description in python_packages:
        if not check_python_package(package, description):
            missing_deps.append(description)
    
    # Check GTK4 Python bindings
    print("\nGTK4 Python Bindings:")
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        gi.require_version('Adw', '1.0')
        from gi.repository import Gtk, Adw
        print(f"✅ GTK4 Python Bindings: Working (GTK {Gtk.MAJOR_VERSION}.{Gtk.MINOR_VERSION})")
    except Exception as e:
        print(f"❌ GTK4 Python Bindings: Failed - {e}")
        missing_deps.append("GTK4 Python bindings")
    
    # Summary
    print("\n" + "=" * 50)
    if missing_deps:
        print("❌ Missing Dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        
        print("\n📋 Installation Instructions:")
        print("1. Run the setup script: ./scripts/setup_dev_environment.sh")
        print("2. Or install manually:")
        print("   sudo apt update")
        print("   sudo apt install -y meson ninja-build libgtk-4-dev libadwaita-1-dev python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1")
        print("   pip install -r requirements.txt")
        
        return 1
    else:
        print("✅ All dependencies are satisfied!")
        print("\n🚀 Ready to develop System Companion!")
        return 0


if __name__ == "__main__":
    sys.exit(main()) 