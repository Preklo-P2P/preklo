#!/usr/bin/env python3
"""
Railway entry point for Preklo backend
This file allows Railway to detect and start the FastAPI application
"""

import os
import sys
import subprocess

def main():
    """Start the FastAPI application"""
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    
    # Get port from environment (Railway provides this)
    port = os.environ.get('PORT', '8000')
    
    # Start uvicorn
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'app.main:app',
        '--host', '0.0.0.0',
        '--port', port
    ]
    
    print(f"Starting Preklo backend on port {port}")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
