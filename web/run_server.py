#!/usr/bin/env python3
"""
Run the FastAPI web server for paper-to-slide generation.

Usage:
    python web/run_server.py
    python web/run_server.py --host 0.0.0.0 --port 8000
"""

import argparse
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Paper to Slide Generator web server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    # Change to project root directory to ensure imports work
    import os
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    try:
        # Use absolute import path
        uvicorn.run(
            "web.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            reload_dirs=[str(project_root)] if args.reload else None
        )
    finally:
        os.chdir(original_cwd)

