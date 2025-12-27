#!/bin/bash
# Simple wrapper to ensure we're in the right directory

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project root (parent of scripts directory)
cd "$SCRIPT_DIR"

# Set API key if not already set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Error: GOOGLE_API_KEY environment variable not set"
    echo "Please set it with: export GOOGLE_API_KEY='your-key-here'"
    exit 1
fi

# Default values
PDF_PATH="${1:-/home/ukenryu/python_try_new/paper2slide/2405.01533v2.pdf}"
OUTPUT_DIR="${2:-presentations/output}"

echo "======================================"
echo "Paper-to-Slides Generation"
echo "======================================"
echo "Working directory: $(pwd)"
echo "PDF: $PDF_PATH"
echo "Output: $OUTPUT_DIR"
echo ""

# Check if PDF exists
if [ ! -f "$PDF_PATH" ]; then
    echo "Error: PDF file not found: $PDF_PATH"
    exit 1
fi

# Make sure we're using the correct Python path
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Run the generation script
python3 scripts/generate_slides.py \
    --pdf "$PDF_PATH" \
    --output "$OUTPUT_DIR"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✓ SUCCESS!"
    echo "======================================"
    echo "Slides saved to: $OUTPUT_DIR"
    echo ""
    echo "View slides:"
    echo "  ls $OUTPUT_DIR/slide_*.png"
    echo ""
    echo "View metadata:"
    echo "  cat $OUTPUT_DIR/presentation_metadata.json | python3 -m json.tool"
else
    echo ""
    echo "======================================"
    echo "✗ FAILED (exit code: $EXIT_CODE)"
    echo "======================================"
    echo "Check logs:"
    echo "  cat logs/paper_to_slides.log"
    echo "  cat logs/errors.log"
fi

exit $EXIT_CODE
