# Figure Analysis Implementation - User Guide

## 🎯 Quick Answer

**Your observation is correct!** PDF image extraction is poor for academic papers. **The system now uses Gemini's direct PDF analysis instead** - this is much better!

---

## 🔧 What Changed

### Before (Problematic)
```bash
./run_generation.sh --pdf paper.pdf --output output/
# ❌ Extracted image fragments
# ❌ Multi-panel figures split up
# ❌ Lost labels and captions
```

### After (Fixed)
```bash
./run_generation.sh --pdf paper.pdf --output output/
# ✅ Gemini "sees" complete figures
# ✅ Understands multi-panel layouts  
# ✅ Reads labels, captions, tables
# ✅ Describes semantic meaning
```

---

## 🚀 How to Use

### Default (Recommended)
Just run normally - Gemini analysis is now the default:
```bash
cd /workspace
export GOOGLE_API_KEY="your-key"
./run_generation.sh --pdf your_paper.pdf --output presentations/output/
```

**What happens:**
1. PDF metadata and text extracted
2. **Gemini analyzes figures directly from PDF** ← NEW!
3. Paper analysis with structured output
4. Presentation plan created
5. Slides generated

### If You Want Old Behavior (Not Recommended)
```bash
./run_generation.sh --pdf paper.pdf --output output/ --extract-images
```

---

## 📊 Why This is Better

### The Problem You Identified
Academic papers store figures as:
- Vector graphics (SVG elements)
- Multiple layered objects
- Separate text and shapes

When PyMuPDF tries to "extract images", it gets:
```
Figure 1 (3-panel architecture diagram)
  ↓ PyMuPDF extraction
├── fragment_1.png (a blue box)
├── fragment_2.png (an arrow)  
├── fragment_3.png (part of text)
└── fragment_4.png (another box)
❌ No complete figure!
```

### The Solution
Gemini's multimodal model can:
```
Figure 1 (3-panel architecture diagram)
  ↓ Gemini analysis  
✅ "A three-panel diagram showing system architecture.
   Left panel: data preprocessing pipeline with...
   Center panel: neural network layers with...
   Right panel: output classification with..."
```

---

## 💡 Technical Details

### What Gemini Returns

For each figure, you get:
```python
{
    "page_number": 3,
    "figure_number": "Figure 1",
    "figure_type": "multi-panel diagram",
    "visual_description": "Three-panel layout with...",
    "content_description": "Shows the system architecture...",
    "importance": 0.95,
    "presentation_usage": "Use for system overview slide"
}
```

### Integration with Slide Generation

These descriptions are passed to the presentation planner:
```python
planner.create_plan(
    paper_analysis,
    pdf_metadata,
    saved_images=[],  # No extraction needed!
    figure_descriptions  # From Gemini
)
```

The planner uses this to:
- Decide which figures to reference
- Write appropriate slide content
- Generate accurate image prompts
- Maintain semantic coherence

---

## ⚡ Performance

### Speed
- **Gemini Analysis**: ~10-15 seconds per PDF (one API call)
- **Old Extraction**: ~1-2 seconds (but poor quality)

**Tradeoff**: Slightly slower but MUCH better results

### Cost
- **Gemini Analysis**: Uses Gemini API tokens
- **Old Extraction**: Free (local processing)

**Tradeoff**: Small API cost for dramatically better quality

---

## 🎓 Use Cases

### Perfect For (Use Gemini Analysis)
- ✅ Academic papers
- ✅ Technical reports
- ✅ Conference papers
- ✅ Papers with multi-panel figures
- ✅ Documents with tables
- ✅ Diagrams with labels

### Maybe Use Extraction
- Photos/raster images only
- Simple documents
- Offline processing required
- Cost is critical

**For your use case (academic papers): Gemini analysis is strongly recommended and is now the default!**

---

## 📝 Example

### Input PDF
```
Page 3: Figure 1
┌─────────────────────────────────────────┐
│ (a) Architecture  │ (b) Results         │
│ ┌──┐  ┌──┐  ┌──┐ │ ┌──────────────┐   │
│ │In├─→│NN├─→│Out││ │ Accuracy: 92%│   │
│ └──┘  └──┘  └──┘ │ └──────────────┘   │
└─────────────────────────────────────────┘
```

### Old Method (Extraction)
```
Extracted: 
- page3_img_1.png (In box)
- page3_img_2.png (arrow)
- page3_img_3.png (NN box)
...
Result: 8 fragments, none useful
```

### New Method (Gemini)
```json
{
  "page_number": 3,
  "figure_number": "Figure 1",
  "figure_type": "multi-panel diagram",
  "visual_description": "Two-panel figure. Left panel (a) shows a system architecture with three boxes labeled 'Input', 'Neural Network', and 'Output' connected by arrows. Right panel (b) displays a results box showing 'Accuracy: 92%'.",
  "content_description": "Illustrates the proposed neural network architecture and its performance. The architecture uses a three-stage pipeline achieving 92% accuracy.",
  "importance": 0.95,
  "presentation_usage": "Use this for the 'System Overview' and 'Results' slides. Split into two slides if needed."
}
```

**Much better!** ✅

---

## 🔄 Migration

No action needed! The system automatically uses the new method.

If you have old cached data with extracted images:
```bash
# Clear cache to use new method
rm -rf .cache/
./run_generation.sh --pdf paper.pdf --output output/
```

---

## 🐛 Troubleshooting

### "Gemini figure analysis failed"
- Check API key is set
- Check PDF is valid
- Check internet connection
- Fallback: System will continue without figure descriptions

### "Want to use old extraction method"
```bash
./run_generation.sh --pdf paper.pdf --output output/ --extract-images
```

---

## 📚 Documentation

- **Implementation Details**: `.cursor/gemini_figure_analysis.md`
- **Code Changes**: See git diff
- **API Usage**: `src/llm/gemini_client.py`
- **Schema Definitions**: `src/utils/models.py`

---

## ✅ Summary

**Problem**: PDF extraction gives fragments, not complete figures  
**Solution**: Use Gemini's vision to analyze PDF directly  
**Status**: ✅ Implemented and default  
**Action Required**: None - works out of the box!  

**Your academic papers will now have much better figure analysis! 🎉**
