#!/usr/bin/env python3
"""
Railway startup script for Preklo backend
Handles environment setup and graceful startup
"""

import os
import sys
import subprocess
import time

def setup_environment():
    """Set up environment variables for Railway deployment"""
    # Set default values if not provided
    if not os.environ.get('DATABASE_URL'):
        print("DATABASE_URL not set - using default")
        os.environ['DATABASE_URL'] = 'postgresql://postgres:password@localhost:5432/preklo'
    
    if not os.environ.get('SECRET_KEY'):
        print("SECRET_KEY not set - using default")
        os.environ['SECRET_KEY'] = 'railway-default-secret-key-change-in-production'
    
    if not os.environ.get('APTOS_NODE_URL'):
        print("APTOS_NODE_URL not set - using testnet")
        os.environ['APTOS_NODE_URL'] = 'https://fullnode.testnet.aptoslabs.com/v1'
    
    if not os.environ.get('APTOS_FAUCET_URL'):
        print("APTOS_FAUCET_URL not set - using testnet")
        os.environ['APTOS_FAUCET_URL'] = 'https://faucet.testnet.aptoslabs.com'

def main():
    """Start the FastAPI application"""
    print("Starting Preklo backend on Railway...")
    
    # Setup environment
    setup_environment()
    
    # Run database migrations from root directory (where alembic.ini is located)
    print("Running database migrations...")
    db_url = os.environ.get('DATABASE_URL', 'NOT SET')
    if db_url != 'NOT SET':
        print(f"Using DATABASE_URL: {db_url[:50]}...")
    else:
        print("WARNING: DATABASE_URL not set - migrations will fail")
    
    try:
        # Ensure environment variables are passed to the subprocess
        env = os.environ.copy()
        result = subprocess.run(
            [sys.executable, '-m', 'alembic', 'upgrade', 'head'],
            check=True,
            env=env,
            capture_output=True,
            text=True
        )
        print("Database migrations completed successfully")
        if result.stdout:
            print(f"Migration output: {result.stdout[:200]}")
    except subprocess.CalledProcessError as e:
        print(f"Migration failed with exit code {e.returncode}")
        if e.stdout:
            print(f"Migration stdout: {e.stdout[:500]}")
        if e.stderr:
            print(f"Migration stderr: {e.stderr[:500]}")
        print("WARNING: Continuing without migrations - app may not work correctly")
        print("Please run migrations manually: railway run alembic upgrade head")
    except Exception as e:
        print(f"Migration error: {e}")
        print("WARNING: Continuing without migrations - app may not work correctly")
    
    # Change to backend directory for uvicorn
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    
    # Get port from environment (Railway provides this)
    port = os.environ.get('PORT', '8000')
    
    print(f"Starting server on port {port}")
    print(f"Health check: http://0.0.0.0:{port}/health")
    
    # Start uvicorn
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'app.main:app',
        '--host', '0.0.0.0',
        '--port', port,
        '--log-level', 'info'
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
