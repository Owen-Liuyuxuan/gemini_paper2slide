#!/bin/bash
# Test script for paper-to-slides generation

# Ensure API key is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Error: GOOGLE_API_KEY environment variable not set"
    echo "Please set it with: export GOOGLE_API_KEY='your-key-here'"
    exit 1
fi

# Ensure PDF path is provided or use default
PDF_PATH="${1:-/home/ukenryu/python_try_new/paper2slide/2405.01533v2.pdf}"
OUTPUT_DIR="${2:-presentations/output}"

echo "======================================"
echo "Paper-to-Slides Generation Test"
echo "======================================"
echo "PDF: $PDF_PATH"
echo "Output: $OUTPUT_DIR"
echo ""

# Check if PDF exists
if [ ! -f "$PDF_PATH" ]; then
    echo "Error: PDF file not found: $PDF_PATH"
    exit 1
fi

# Run the generation script
python scripts/generate_slides.py \
    --pdf "$PDF_PATH" \
    --output "$OUTPUT_DIR"

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✓ Generation successful!"
    echo "======================================"
    echo "Output directory: $OUTPUT_DIR"
    echo "View slides: ls $OUTPUT_DIR/slide_*.png"
    echo "View metadata: cat $OUTPUT_DIR/presentation_metadata.json"
else
    echo ""
    echo "======================================"
    echo "✗ Generation failed"
    echo "======================================"
    echo "Check logs: logs/paper_to_slides.log"
    echo "Check errors: logs/errors.log"
    exit 1
fi
