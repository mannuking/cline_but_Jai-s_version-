#!/usr/bin/env python
"""
Script to install dependencies without requiring Rust compiler
This script uses pre-compiled binary wheels for packages that otherwise require Rust
"""
import subprocess
import sys
import platform
import os

def install_requirements():
    print("Installing dependencies without requiring Rust...")
    
    # First install all packages that don't have Rust dependencies
    packages = [
        "streamlit==1.29.0",
        "streamlit-ace==0.1.1",
        "pexpect==4.8.0",
        "firebase-admin==6.2.0", 
        "python-dotenv==1.0.0",
        "watchdog==3.0.0",
        "streamlit-tree-select==0.0.5",
        "zipfile36==0.1.3",
        "pyyaml==6.0.1"
    ]
    
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
    print("✓ Installed main dependencies")
    
    # Now install tokenizers with the --no-build-isolation flag
    try:
        # First try installing anthropic with a version that doesn't need tokenizers
        print("Installing anthropic with a compatible version...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic==0.5.0"])
        print("✓ Installed anthropic")
    except subprocess.CalledProcessError:
        print("Failed to install anthropic, trying alternative approach...")
        
        # If that doesn't work, try with a more direct approach using wheels
        try:
            # For Windows platform
            if platform.system() == "Windows":
                print("Installing pre-compiled tokenizers for Windows...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", 
                                      "https://download.pytorch.org/whl/cpu/tokenizers-0.13.2-cp310-cp310-win_amd64.whl"])
            # For macOS platform
            elif platform.system() == "Darwin":
                print("Installing pre-compiled tokenizers for macOS...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "tokenizers"])
            # For Linux platform
            else:
                print("Installing tokenizers with apt dependencies...")
                # Make sure the required libraries are installed
                try:
                    subprocess.check_call(["apt-get", "update"])
                    subprocess.check_call(["apt-get", "install", "-y", "build-essential", "curl"])
                except:
                    print("Note: Could not update apt packages. If you're not on a Debian-based system, this is expected.")
                
                # Try installing with --no-build-isolation
                subprocess.check_call([sys.executable, "-m", "pip", "install", 
                                      "tokenizers", "--no-build-isolation"])
            
            # Now try installing anthropic again
            subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic==0.7.4"])
            print("✓ Installed tokenizers and anthropic")
        except subprocess.CalledProcessError:
            print("❌ Could not install tokenizers. Please install Rust from https://rustup.rs/")
            print("Falling back to anthropic version that doesn't require tokenizers")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic==0.4.3"])
    
    print("✓ All dependencies installed!")

if __name__ == "__main__":
    install_requirements()
