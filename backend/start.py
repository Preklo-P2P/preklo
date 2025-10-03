#!/usr/bin/env python3
"""
Preklo Backend Startup Script
Alternative Python-based startup for the backend server
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("Starting Preklo Backend...")
    
    # Check if we're in the backend directory
    if not Path("app/main.py").exists():
        print("Error: This script must be run from the backend directory")
        print("Please run: cd /path/to/Preklo/backend && python start.py")
        sys.exit(1)
    
    # Check if virtual environment exists
    venv_path = Path("../venv")
    if not venv_path.exists():
        print("Error: Virtual environment not found at ../venv")
        print("Please run the setup script from the project root first")
        sys.exit(1)
    
    # Set environment variables
    print("Setting up environment...")
    
    # Add backend to Python path
    backend_path = str(Path.cwd().absolute())
    os.environ['PYTHONPATH'] = backend_path
    
    # Load .env file if it exists
    env_file = Path("../.env")
    if env_file.exists():
        print("📋 Loading environment variables from .env...")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    else:
        print("No .env file found, using default configuration")
    
    print("Starting server on http://localhost:8000...")
    print("API documentation will be available at http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("")
    
    try:
        # Start the FastAPI server
        subprocess.run([
            sys.executable, "-m", "app.main"
        ], check=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
