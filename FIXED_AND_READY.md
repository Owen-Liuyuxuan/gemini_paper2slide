# Fixed Issues & How to Run

## ✅ Fixed Issues

### 1. Logger Bug Fixed
**Problem**: `UnboundLocalError: local variable 'logger' referenced before assignment`

**Solution**: Renamed the imported logger to `_logger` to avoid variable shadowing.

**File**: `src/utils/logger.py` - Now working correctly!

---

## 🚀 How to Run

### Option 1: Use the provided test script

```bash
# Make sure API key is set
export GOOGLE_API_KEY="AIzaSyCJKQ76H09uFaiea6GlKf23wTYfM72ZhtY"

# Run with default PDF path
./test_generation.sh

# Or specify custom PDF and output
./test_generation.sh /path/to/your/paper.pdf /path/to/output/
```

### Option 2: Run directly with Python

```bash
# Set API key
export GOOGLE_API_KEY="AIzaSyCJKQ76H09uFaiea6GlKf23wTYfM72ZhtY"

# Generate slides
python scripts/generate_slides.py \
    --pdf /home/ukenryu/python_try_new/paper2slide/2405.01533v2.pdf \
    --output presentations/output/
```

### Option 3: Run local tests (to verify setup)

```bash
# This tests the system without generating slides
python scripts/test_local.py
```

---

## 📋 Command Line Options

```bash
python scripts/generate_slides.py \
    --pdf <path_to_pdf>           # Required: PDF file to process
    --output <output_directory>   # Required: Where to save slides
    --no-cache                    # Optional: Disable caching (for testing)
    --resume                      # Optional: Resume from checkpoint
    --no-describe-images          # Optional: Skip image descriptions (faster)
```

---

## Expected Output

When successful, you'll see:

```
================================================================================
Starting slide generation for: /home/ukenryu/python_try_new/paper2slide/2405.01533v2.pdf
Output directory: presentations/output
Cache: enabled
Resume: no
================================================================================

================================================================================
STEP 1: Extracting PDF content...
================================================================================
✓ Extracted 15 pages, 8934 words
✓ Title: Paper Title
✓ Authors: Author Names
✓ Extracted 23 images from PDF
✓ Filtered to 12 high-quality images
✓ Saved 12 images

... (more steps)

================================================================================
✓ SLIDE GENERATION COMPLETE!
================================================================================
Successfully generated 10 slides
Output directory: /workspace/presentations/output
Slides: /workspace/presentations/output/slide_*.png
Metadata: /workspace/presentations/output/presentation_metadata.json
================================================================================
```

Your slides will be in `presentations/output/`:
- `slide_00.title.png`
- `slide_01.content.png`
- `slide_02.content.png`
- etc.

---

## ⚠️ Common Issues

### Issue: PDF Not Found
```
FileNotFoundError: PDF file not found: ...
```

**Solution**: Use absolute path or verify the file exists:
```bash
ls -l /home/ukenryu/python_try_new/paper2slide/2405.01533v2.pdf
```

### Issue: API Key Error
```
ValueError: Google API key not provided
```

**Solution**: Ensure environment variable is set:
```bash
echo $GOOGLE_API_KEY  # Should print your key
export GOOGLE_API_KEY="your-key-here"
```

### Issue: Module Not Found
```
ModuleNotFoundError: No module named 'google'
```

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Permission Denied
```
PermissionError: [Errno 13] Permission denied: 'presentations/output'
```

**Solution**: Create output directory or use different location:
```bash
mkdir -p presentations/output
# or
python scripts/generate_slides.py --pdf paper.pdf --output ~/my_slides/
```

---

## 🐛 Debugging

If generation fails:

1. **Check logs**:
   ```bash
   cat logs/paper_to_slides.log  # All logs
   cat logs/errors.log            # Errors only
   ```

2. **Run with verbose output**:
   ```bash
   # Logs are already verbose by default
   # Check the console output
   ```

3. **Test components**:
   ```bash
   python scripts/test_local.py  # Tests without PDF processing
   ```

4. **Check API quota**:
   - Ensure you haven't hit rate limits
   - Check API key is valid
   - Verify billing is enabled (if using paid tier)

---

## 📊 Performance

Expected times for a typical paper (10-20 pages):
- PDF Extraction: 5-10 seconds
- Paper Analysis: 30-60 seconds
- Image Descriptions: 1-2 minutes (if enabled)
- Presentation Planning: 30-60 seconds
- Slide Generation: 5-10 minutes (depends on slide count)

**Total**: ~8-15 minutes for a typical paper

---

## 💡 Tips

1. **First run**: Test with a small PDF (5-10 pages) to verify setup
2. **Use cache**: Don't use `--no-cache` unless debugging
3. **Skip descriptions**: Use `--no-describe-images` for faster generation
4. **Monitor progress**: Watch the console output for progress indicators
5. **Resume capability**: If interrupted, use `--resume` to continue

---

## ✅ All Systems Go!

The logger bug is fixed. You're ready to generate slides! 🎉

Try running:
```bash
./test_generation.sh
```

Or directly:
```bash
export GOOGLE_API_KEY="AIzaSyCJKQ76H09uFaiea6GlKf23wTYfM72ZhtY"
python scripts/generate_slides.py \
    --pdf /home/ukenryu/python_try_new/paper2slide/2405.01533v2.pdf \
    --output presentations/output/
```
