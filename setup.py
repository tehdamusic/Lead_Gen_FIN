#!/usr/bin/env python3
"""
Lead Generation Tool setup script.
This script configures the directory structure and installs dependencies.
"""

import os
import sys
import subprocess
from pathlib import Path

def create_directory_structure():
    """Create the necessary directories for the application."""
    print("Creating directory structure...")
    
    # Create main directories
    directories = [
        "config",
        "data",
        "data/cache",
        "data/output",
        "logs",
        "scrapers",
        "analysis",
        "communication",
        "reporting",
        "gui",
        "utils"
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(exist_ok=True)
        print(f"✓ Created {directory}/")
    
    # Create __init__.py files
    init_dirs = [
        "scrapers",
        "analysis",
        "communication",
        "reporting",
        "gui",
        "utils"
    ]
    
    for directory in init_dirs:
        init_file = Path(directory) / "__init__.py"
        if not init_file.exists():
            with open(init_file, 'w') as f:
                f.write(f'"""\n{directory.capitalize()} modules for the Lead Generation Tool.\n"""\n')
            print(f"✓ Created {init_file}")
    
    print("Directory structure created successfully.")

def install_dependencies():
    """Install Python dependencies from requirements.txt."""
    print("Installing dependencies...")
    
    if not Path("requirements.txt").exists():
        print("Error: requirements.txt not found.")
        return False
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {str(e)}")
        return False

def create_env_file():
    """Create a .env file from .env.example if it doesn't exist."""
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("Creating .env file from template...")
            
            with open(".env.example", 'r') as source:
                content = source.read()
            
            with open(".env", 'w') as target:
                target.write(content)
            
            print("✓ Created .env file. Please edit it with your credentials.")
        else:
            print("Warning: .env.example not found, cannot create .env file.")
    else:
        print("✓ .env file already exists.")

def main():
    """Main setup function."""
    print("\n=== Lead Generation Tool Setup ===\n")
    
    # Create directory structure
    create_directory_structure()
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    if install_dependencies():
        print("\nSetup completed successfully!")
        print("\nNext steps:")
        print("1. Edit the .env file with your API credentials")
        print("2. Place your Google API credentials.json file in the config/ directory")
        print("3. Run the application with: python main.py gui")
    else:
        print("\nSetup completed with errors. Please fix the issues and try again.")
    
    print("\n===================================\n")

if __name__ == "__main__":
    main()
