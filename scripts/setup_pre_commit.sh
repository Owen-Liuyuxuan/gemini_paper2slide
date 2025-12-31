#!/bin/bash
# Setup script for pre-commit hooks

set -e

echo "Setting up pre-commit hooks..."

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install uv first."
    echo "Visit: https://github.com/astral-sh/uv"
    exit 1
fi

# Install pre-commit if not already installed
echo "Installing pre-commit..."
uv add --dev pre-commit

# Install git hooks
echo "Installing git hooks..."
uv run pre-commit install

echo ""
echo "✅ Pre-commit hooks installed successfully!"
echo ""
echo "The following hooks will run on git commit:"
echo "  - Black (code formatting)"
echo "  - Ruff (linting and auto-fixes)"
echo "  - Ruff Format (code formatting)"
echo "  - MyPy (type checking)"
echo "  - General file checks (trailing whitespace, etc.)"
echo ""
echo "To test hooks manually, run:"
echo "  uv run pre-commit run --all-files"
