#!/bin/bash
# Wrapper script to run slide generation from project root

# Get script directory and change to it
cd "$(dirname "$0")"

echo "Working directory: $(pwd)"

# Check API key
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Error: GOOGLE_API_KEY not set"
    exit 1
fi

# Run with Python path set
PYTHONPATH="$(pwd):$PYTHONPATH" python3 scripts/generate_slides.py "$@"
