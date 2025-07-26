#!/usr/bin/env python3
"""
System Companion - Launcher Script

This script launches System Companion with the correct Python path setup.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Set environment variable for the application
os.environ["SYSTEM_COMPANION_APP"] = "1"

# Import and run the main application
from system_companion.main import main

if __name__ == "__main__":
    sys.exit(main()) 