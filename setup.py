#!/usr/bin/env python3
"""
Smart Inventory & Warehouse Management System
Setup Script - Run this before launching the application
"""

import subprocess
import sys
import os

REQUIRED_PACKAGES = [
    "pillow",
    "python-barcode",
    "reportlab",
    "matplotlib",
    "pandas",
    "openpyxl",
    "qrcode",
    "ttkbootstrap",
]

def install_packages():
    print("=" * 60)
    print("  Smart Inventory & Warehouse Management System - Setup")
    print("=" * 60)
    print("\nInstalling required packages...\n")
    for pkg in REQUIRED_PACKAGES:
        print(f"  Installing {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])
        print(f"  ✓ {pkg} installed")
    print("\n✓ All packages installed successfully!")

def create_data_dirs():
    dirs = ["data", "assets", "reports", "data/barcodes"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("✓ Data directories created!")

if __name__ == "__main__":
    install_packages()
    create_data_dirs()
    print("\n✓ Setup complete! Run: python main.py\n")
