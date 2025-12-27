# Quick Start Guide: PDF-to-Slides System

**Version**: 2.0 (Refactored)  
**Date**: 2025-12-27

---

## Prerequisites

### 1. Install Dependencies

```bash
cd /workspace
pip install -r requirements.txt
```

### 2. Set Up API Key

```bash
# Set your Google Gemini API key
export GOOGLE_API_KEY="your-gemini-api-key-here"

# Or create a .env file
echo "GOOGLE_API_KEY=your-gemini-api-key-here" > .env
```

---

## Basic Usage

### Generate Slides from a PDF

```bash
python scripts/generate_slides.py \
    --pdf path/to/your/paper.pdf \
    --output output/my_presentation/
```

### What Happens:
1. ✅ Extracts text and images from PDF
2. ✅ Analyzes paper with Gemini (generates descriptions)
3. ✅ Creates structured presentation plan
4. ✅ Generates slides with visual consistency
5. ✅ Saves slides and metadata

### Output:
```
output/my_presentation/
├── slide_00.title.png          # Title slide
├── slide_01.content.png        # Content slides
├── slide_02.content.png
├── ...
├── presentation_metadata.json  # Metadata with all info
└── extracted_images/           # Images from PDF
    ├── extracted_p0_i0.png
    └── ...
```

---

## Advanced Usage

### Disable Caching (for testing)

```bash
python scripts/generate_slides.py \
    --pdf paper.pdf \
    --output output/ \
    --no-cache
```

### Skip Image Descriptions (faster)

```bash
python scripts/generate_slides.py \
    --pdf paper.pdf \
    --output output/ \
    --no-describe-images
```

**Note**: Skipping image descriptions is faster but may result in less accurate figure-to-slide matching.

### Resume After Interruption

```bash
# If generation was interrupted (Ctrl+C or crash)
python scripts/generate_slides.py \
    --pdf paper.pdf \
    --output output/ \
    --resume
```

**Note**: Partial resume support. Some steps may need to re-run.

---

## Example Session

### Complete Example

```bash
# 1. Set API key
export GOOGLE_API_KEY="AIza..."

# 2. Generate slides
python scripts/generate_slides.py \
    --pdf papers/deep_learning_survey.pdf \
    --output presentations/dl_survey/

# 3. Check the output
ls presentations/dl_survey/
# slide_00.title.png
# slide_01.content.png
# ...
# presentation_metadata.json

# 4. View metadata
cat presentations/dl_survey/presentation_metadata.json | jq '.'
```

---

## Expected Output

### Console Output

```
================================================================================
Starting slide generation for: papers/deep_learning_survey.pdf
Output directory: presentations/dl_survey
Cache: enabled
Resume: no
================================================================================

================================================================================
STEP 1: Extracting PDF content...
================================================================================
✓ Extracted 15 pages, 8934 words
✓ Title: Deep Learning for Computer Vision: A Survey
✓ Authors: John Doe, Jane Smith
✓ Extracted 23 images from PDF
✓ Filtered to 12 high-quality images
✓ Saved 12 images

================================================================================
STEP 2: Analyzing paper with Gemini...
================================================================================
✓ Paper analysis complete
  - Research Question: How have deep learning methods evolved for computer vision...
  - Key Points: 7
  - Recommended Slides: 10

Generating image descriptions...
✓ Described 10 images

================================================================================
STEP 3: Creating presentation plan...
================================================================================
✓ Created plan with 10 slides
  - Slide 0: Deep Learning for Computer Vision: A Survey (title)
  - Slide 1: Introduction and Motivation (content)
  - Slide 2: Evolution of Deep Learning Methods (content)
  ... and 7 more slides

================================================================================
STEP 4: Generating slides...
================================================================================
This may take several minutes depending on the number of slides...

STAGE 1: Generating title slide with style extraction
✓ Title slide generated, style extracted for consistency

STAGE 2: Generating 9 content slides with style consistency
Generating slide 1/10: Introduction and Motivation
✓ Slide 1 generated successfully
Generating slide 2/10: Evolution of Deep Learning Methods
✓ Slide 2 generated successfully
...

✓ Completed slide generation: 10/10 slides successful

================================================================================
STEP 5: Saving outputs...
================================================================================
✓ Saved 10 slide images
✓ Saved presentation metadata

================================================================================
✓ SLIDE GENERATION COMPLETE!
================================================================================
Successfully generated 10 slides
Output directory: /workspace/presentations/dl_survey
Slides: /workspace/presentations/dl_survey/slide_*.png
Metadata: /workspace/presentations/dl_survey/presentation_metadata.json
================================================================================
```

---

## Troubleshooting

### API Key Not Set

**Error**:
```
ValueError: Google API key not provided. Set GOOGLE_API_KEY environment variable
```

**Solution**:
```bash
export GOOGLE_API_KEY="your-key-here"
# or add to .env file
```

### PDF Not Found

**Error**:
```
FileNotFoundError: PDF file not found: paper.pdf
```

**Solution**:
```bash
# Use absolute path or correct relative path
python scripts/generate_slides.py \
    --pdf /full/path/to/paper.pdf \
    --output output/
```

### Out of Memory

**Error**:
```
MemoryError: Unable to allocate array
```

**Solution**:
```bash
# Skip image descriptions to save memory
python scripts/generate_slides.py \
    --pdf paper.pdf \
    --output output/ \
    --no-describe-images
```

### Rate Limit Hit

**Error**:
```
429 Too Many Requests
```

**Solution**:
- Wait a few minutes and try again
- Use `--resume` to continue from last checkpoint
- Consider reducing paper size or number of images

### Generation Interrupted

**Solution**:
```bash
# Resume from last checkpoint
python scripts/generate_slides.py \
    --pdf paper.pdf \
    --output output/ \
    --resume
```

---

## Configuration

### Edit Config Files

```bash
# Main configuration
vim config/config.json

# Key settings:
{
  "gemini": {
    "model_text": "gemini-2.5-flash",      # Text model
    "model_image": "gemini-2.5-flash-image", # Image model
    "temperature": 0.7,                     # Creativity (0.0-1.0)
    "max_retries": 3                        # Retry attempts
  },
  "presentation": {
    "default_slide_count": 10,              # Default slides
    "max_slides": 15,                       # Maximum slides
    "aspect_ratio": "16:9"                  # Slide ratio
  }
}
```

### Environment Variables

```bash
# In .env file
GOOGLE_API_KEY=your-key
CACHE_ENABLED=true
CACHE_DIR=.cache
LOG_LEVEL=INFO
LOG_DIR=logs
```

---

## Performance Tips

### Speed Up Generation

1. **Disable image descriptions**:
   ```bash
   --no-describe-images  # Saves ~1-2 minutes
   ```

2. **Use cache** (default):
   ```bash
   # Analysis is cached by default
   # Second run with same PDF is much faster
   ```

3. **Reduce slides**:
   ```bash
   # Edit config.json
   "presentation": {
     "default_slide_count": 8,  # Fewer slides
     "max_slides": 10
   }
   ```

### Improve Quality

1. **Enable image descriptions** (default):
   ```bash
   # Better figure matching
   # Takes longer but worth it
   ```

2. **Increase temperature**:
   ```bash
   # Edit config.json
   "temperature": 0.8  # More creative (0.7 default)
   ```

3. **Use high-quality PDFs**:
   - Clear text
   - Good image quality
   - Proper formatting

---

## Output Files Explained

### Slide Images

```
slide_00.title.png      # Title slide
slide_01.content.png    # First content slide
slide_02.figure.png     # Slide with figure
slide_09.conclusion.png # Conclusion slide
```

**Naming**: `slide_{index:02d}.{type}.png`

### Metadata JSON

```json
{
  "presentation_info": {
    "title": "Paper Title",
    "authors": ["Author 1", "Author 2"],
    "page_count": 15
  },
  "analysis_info": {
    "research_question": "...",
    "methodology": "...",
    "key_contributions": [...]
  },
  "slide_info": [
    {
      "index": 0,
      "type": "title",
      "title": "...",
      "main_points": [],
      "generation_time": 45.2,
      "size_mb": 2.3
    },
    ...
  ],
  "generation_stats": {
    "total_slides": 10,
    "total_generation_time": 456.7,
    "average_generation_time": 45.67
  }
}
```

### Checkpoint Files

```
.checkpoints/
├── pdf_extraction.json
├── paper_analysis.json
├── presentation_planning.json
├── slide_generation.json
└── complete.json
```

**Purpose**: Allow resuming if interrupted.

---

## Best Practices

### 1. Paper Selection

✅ **Good**:
- Academic papers with clear structure
- Papers with informative figures
- 5-30 pages
- PDF with text (not scanned images)

❌ **Avoid**:
- Scanned PDFs (poor text extraction)
- Papers with complex mathematical notation
- Very short (<5 pages) or very long (>30 pages) papers
- Password-protected PDFs

### 2. First Time Use

```bash
# 1. Test with a small paper first
python scripts/generate_slides.py \
    --pdf small_paper.pdf \
    --output test_output/

# 2. Check the results
ls test_output/
cat test_output/presentation_metadata.json

# 3. If satisfied, process your target paper
python scripts/generate_slides.py \
    --pdf target_paper.pdf \
    --output final_output/
```

### 3. Batch Processing

```bash
# Process multiple papers
for pdf in papers/*.pdf; do
    output_dir="presentations/$(basename $pdf .pdf)"
    python scripts/generate_slides.py \
        --pdf "$pdf" \
        --output "$output_dir/"
done
```

---

## FAQ

### Q: How long does it take?

**A**: 5-15 minutes depending on paper length and options:
- Small paper (5-10 pages): ~5 minutes
- Medium paper (10-20 pages): ~8 minutes
- Large paper (20-30 pages): ~15 minutes

### Q: Can I edit the slides after generation?

**A**: Yes, they're PNG images. Use any image editor or import into PowerPoint/Keynote/Google Slides.

### Q: What if style consistency isn't perfect?

**A**: The system extracts style from the title slide and applies it to other slides. Results are typically 80-90% consistent. For perfect consistency, manually adjust in your presentation software.

### Q: Can I use a different aspect ratio?

**A**: Yes, edit `config/config.json`:
```json
"aspect_ratio": "4:3"  # or "1:1", "9:16", etc.
```

### Q: Do I need a paid Gemini API?

**A**: The free tier should work for testing. For production use, consider the paid tier to avoid rate limits.

### Q: Can I customize the prompts?

**A**: Yes, edit files in `src/llm/prompts/`:
- `paper_analysis.txt`
- `presentation_plan.txt`
- `title_slide.txt`
- `content_slide.txt`

---

## Next Steps

1. ✅ **Try it out**: Generate slides from a sample paper
2. ✅ **Check results**: Review the generated slides and metadata
3. ✅ **Customize**: Adjust config and prompts if needed
4. ✅ **Integrate**: Use in your workflow

---

## Support

### Documentation
- **Review**: `/workspace/.cursor/comprehensive_code_review.md`
- **Plan**: `/workspace/.cursor/refactoring_plan.md`
- **Complete**: `/workspace/.cursor/refactoring_complete.md`

### Logs
- **Location**: `logs/paper_to_slides.log`
- **Errors**: `logs/errors.log`

### Getting Help
1. Check logs for error details
2. Review troubleshooting section above
3. Check configuration files
4. Ensure API key is valid

---

**Happy Presenting!** 🎉

For detailed information, see `/workspace/.cursor/refactoring_complete.md`
