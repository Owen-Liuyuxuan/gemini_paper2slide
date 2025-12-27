# How to Run - Quick Commands

## ✅ Issue Fixed
The module import issue has been fixed. The script now properly sets up the Python path.

---

## 🚀 Running the System

### **Method 1: Using the wrapper script (Easiest)**

```bash
cd /workspace

# Set API key
export GOOGLE_API_KEY="AIzaSyCJKQ76H09uFaiea6GlKf23wTYfM72ZhtY"

# Run with wrapper script
./run_generation.sh \
    --pdf /home/ukenryu/python_try_new/paper2slide/2405.01533v2.pdf \
    --output presentations/output/
```

### **Method 2: Direct Python (from project root)**

```bash
cd /workspace

# Set API key
export GOOGLE_API_KEY="AIzaSyCJKQ76H09uFaiea6GlKf23wTYfM72ZhtY"

# Set Python path and run
PYTHONPATH=/workspace:$PYTHONPATH python3 scripts/generate_slides.py \
    --pdf /home/ukenryu/python_try_new/paper2slide/2405.01533v2.pdf \
    --output presentations/output/
```

### **Method 3: Using python -m (Alternative)**

```bash
cd /workspace

# Set API key
export GOOGLE_API_KEY="AIzaSyCJKQ76H09uFaiea6GlKf23wTYfM72ZhtY"

# Run as module
python3 -m scripts.generate_slides \
    --pdf /home/ukenryu/python_try_new/paper2slide/2405.01533v2.pdf \
    --output presentations/output/
```

---

## 📋 Command Options

### Basic Options
```bash
--pdf PATH              # Path to PDF file (required)
--output PATH           # Output directory (required)
```

### Advanced Options
```bash
--no-cache              # Disable caching (useful for testing)
--resume                # Resume from last checkpoint
--no-describe-images    # Skip image descriptions (faster, less accurate)
```

### Examples

**Fast generation (skip image descriptions)**:
```bash
./run_generation.sh \
    --pdf paper.pdf \
    --output output/ \
    --no-describe-images
```

**Resume after interruption**:
```bash
./run_generation.sh \
    --pdf paper.pdf \
    --output output/ \
    --resume
```

**No caching (for testing)**:
```bash
./run_generation.sh \
    --pdf paper.pdf \
    --output output/ \
    --no-cache
```

---

## 🔧 Quick Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'src'"

**Solution**: Run from project root with PYTHONPATH set:
```bash
cd /workspace
PYTHONPATH=/workspace:$PYTHONPATH python3 scripts/generate_slides.py --pdf paper.pdf --output out/
```

Or use the wrapper script:
```bash
cd /workspace
./run_generation.sh --pdf paper.pdf --output out/
```

### Issue: "Google API key not provided"

**Solution**: Set the environment variable:
```bash
export GOOGLE_API_KEY="AIzaSyCJKQ76H09uFaiea6GlKf23wTYfM72ZhtY"
```

To make it permanent for your session, add to `~/.bashrc`:
```bash
echo 'export GOOGLE_API_KEY="AIzaSyCJKQ76H09uFaiea6GlKf23wTYfM72ZhtY"' >> ~/.bashrc
source ~/.bashrc
```

### Issue: "PDF file not found"

**Solution**: Use absolute path:
```bash
./run_generation.sh \
    --pdf "$(pwd)/2405.01533v2.pdf" \
    --output presentations/output/
```

Or verify the path:
```bash
ls -l /home/ukenryu/python_try_new/paper2slide/2405.01533v2.pdf
```

---

## 📁 Expected Output Structure

After successful generation:

```
presentations/output/
├── slide_00.title.png           # Title slide
├── slide_01.content.png         # Content slides
├── slide_02.content.png
├── slide_03.figure.png          # Slide with figure
├── ...
├── slide_09.conclusion.png      # Conclusion
├── presentation_metadata.json   # Metadata
├── extracted_images/            # Images from PDF
│   ├── extracted_p0_i0.png
│   └── ...
└── .checkpoints/                # Resume checkpoints
    ├── pdf_extraction.json
    ├── paper_analysis.json
    └── ...
```

---

## ⏱️ Expected Runtime

For a typical paper (15 pages):
- **PDF Extraction**: 10 seconds
- **Paper Analysis**: 60 seconds
- **Image Descriptions**: 90 seconds (if enabled)
- **Planning**: 45 seconds
- **Slide Generation**: 8 minutes (for 10 slides)

**Total**: ~10-12 minutes

You can speed it up by using `--no-describe-images` (saves ~90 seconds)

---

## 📊 Checking Progress

### Watch the logs in real-time:
```bash
tail -f logs/paper_to_slides.log
```

### Check for errors:
```bash
cat logs/errors.log
```

### View latest checkpoint:
```bash
ls -lt presentations/output/.checkpoints/ | head -5
```

---

## ✅ Verification Commands

### After generation completes:

```bash
# List generated slides
ls -lh presentations/output/slide_*.png

# Count slides
ls presentations/output/slide_*.png | wc -l

# View metadata
cat presentations/output/presentation_metadata.json | python3 -m json.tool | head -50

# Check slide info
python3 << EOF
import json
with open('presentations/output/presentation_metadata.json') as f:
    data = json.load(f)
print(f"Title: {data['presentation_info']['title']}")
print(f"Total slides: {data['generation_stats']['total_slides']}")
print(f"Total time: {data['generation_stats']['total_generation_time']:.1f}s")
EOF
```

---

## 🎯 Ready to Generate!

**Recommended first command**:

```bash
cd /workspace
export GOOGLE_API_KEY="AIzaSyCJKQ76H09uFaiea6GlKf23wTYfM72ZhtY"
./run_generation.sh \
    --pdf /home/ukenryu/python_try_new/paper2slide/2405.01533v2.pdf \
    --output presentations/output/
```

Then sit back and watch the progress! ☕

The system will:
1. Extract text and images from PDF
2. Analyze the paper with AI
3. Create a structured presentation plan
4. Generate visually consistent slides
5. Save everything to the output directory

Check `presentations/output/` when done! 🎉
