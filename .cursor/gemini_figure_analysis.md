# Gemini Figure Analysis - Design Change

**Date**: 2025-12-27  
**Issue**: PDF image extraction produces poor results for academic papers  
**Solution**: Use Gemini's direct PDF analysis instead

---

## 🔍 Problem Analysis

### The PDF Extraction Issue

As you correctly identified, academic papers have a fundamental problem with traditional PDF image extraction:

1. **Vector Graphics**: Figures are often created in SVG/Illustrator, then compiled into PDF
2. **Layered Structure**: PDF stores them as multiple separate objects (lines, text, shapes)
3. **Extraction Failure**: Tools like PyMuPDF's `extract_images()` get fragments, not complete figures
4. **Poor Quality**: Extracted "images" are often partial, missing components, or just artifacts

### Example
```
Academic Figure (what humans see):
┌─────────────────────────────────┐
│  Multi-panel figure with:       │
│  - Chart with axes and labels   │
│  - Diagram with arrows          │
│  - Table with data              │
│  - Caption text                 │
└─────────────────────────────────┘

PDF Extraction (what PyMuPDF gets):
├── fragment_1.png (partial chart, no labels)
├── fragment_2.png (just an arrow)
├── fragment_3.png (random color patch)
└── fragment_4.png (part of a table border)
```

---

## ✅ Solution: Gemini's Direct PDF Analysis

### Why This is Better

Gemini's multimodal capabilities can:
1. **"See" the entire PDF** as humans do - complete figures, layout, context
2. **Understand visual relationships** - what elements belong together
3. **Read text overlays** - captions, labels, axes
4. **Describe semantically** - what the figure *means*, not just pixels
5. **No fragmentation** - analyzes the composed visual output

### Technical Approach

```python
# OLD WAY (problematic)
images = pymupdf.extract_images(pdf)  # Gets fragments
filtered = filter_by_quality(images)   # Still fragments
descriptions = gemini.describe_image(filtered)  # Describing fragments

# NEW WAY (recommended)
figure_analysis = gemini.analyze_figures_from_pdf(pdf)
# Returns: Complete descriptions of all figures as they appear in the PDF
```

---

## 🛠️ Implementation Changes

### 1. New Data Models (`src/utils/models.py`)

```python
class FigureDescriptionSchema(BaseModel):
    """Gemini's description of a figure/table from PDF."""
    page_number: int
    figure_number: Optional[str]  # "Figure 1", "Table 2", etc.
    figure_type: str  # "chart", "diagram", "table", etc.
    visual_description: str  # What it looks like
    content_description: str  # What it shows/means
    importance: float  # 0-1
    presentation_usage: str  # How to use in slides

class PaperFiguresSchema(BaseModel):
    """Complete figure analysis from PDF."""
    total_figures: int
    figures: List[FigureDescriptionSchema]
```

### 2. DocumentAnalyzer Enhancement

Added new method:
```python
def analyze_figures_from_pdf(self, pdf_path: Path) -> Dict[int, str]:
    """
    Analyze all figures/tables directly from PDF using Gemini's vision.
    
    Avoids the PDF extraction problem by letting Gemini "see" the PDF
    as it appears visually, not as fragmented vector elements.
    """
```

### 3. GeminiClient Update

Enhanced `generate_structured_output` to accept PDF files:
```python
def generate_structured_output(
    self,
    prompt: str,
    response_schema: type[BaseModel],
    pdf_path: Optional[Path] = None,  # NEW!
    ...
) -> BaseModel:
    if pdf_path:
        # Upload PDF and analyze with structured output
        file_ref = self.client.files.upload(path=str(pdf_path))
        content = [file_ref, prompt]
    ...
```

### 4. Main Script Changes

**New Arguments**:
```bash
# Recommended (default)
./run_generation.sh --pdf paper.pdf --output output/

# Use old method (not recommended)
./run_generation.sh --pdf paper.pdf --output output/ --extract-images
```

**Workflow Change**:
```
OLD:
1. Extract PDF images (gets fragments)
2. Filter by quality (still fragments)
3. Describe fragments with Gemini
4. Use in slide generation

NEW:
1. Skip extraction entirely  
2. Let Gemini analyze PDF directly
3. Get complete figure descriptions
4. Use in slide generation
```

---

## 📊 Comparison

| Aspect | PDF Extraction | Gemini Analysis |
|--------|---------------|-----------------|
| **Quality** | ❌ Poor (fragments) | ✅ Excellent (complete) |
| **Accuracy** | ❌ Misses components | ✅ Sees full figure |
| **Context** | ❌ No understanding | ✅ Understands meaning |
| **Multi-panel** | ❌ Splits into pieces | ✅ Recognizes as one |
| **Tables** | ❌ Often broken | ✅ Reads correctly |
| **Captions** | ❌ Lost | ✅ Included |
| **Speed** | ⚡ Fast | 🐌 Slower (but better) |
| **Cost** | 💰 Free | 💰💰 API calls |

---

## 🚀 Usage

### Recommended (Default)
```bash
cd /workspace
export GOOGLE_API_KEY="your-key"

# Uses Gemini figure analysis (no --extract-images flag)
./run_generation.sh --pdf paper.pdf --output presentations/output/
```

### Legacy Mode (If you really want it)
```bash
# Force PDF extraction (not recommended for academic papers)
./run_generation.sh --pdf paper.pdf --output presentations/output/ --extract-images
```

---

## 📝 Example Output

### Gemini Figure Analysis Output
```
**Figure 1** (multi-panel diagram)

Visual Description:
A three-panel figure showing: (a) System architecture diagram with blue 
boxes connected by arrows, (b) Performance comparison bar chart with 
red and green bars, (c) Confusion matrix heatmap with gradient from 
white to dark purple

Content:
Demonstrates the proposed method's architecture and performance. Left panel 
shows data flow through preprocessing, feature extraction, and classification 
stages. Middle panel compares accuracy (92% vs 85%) against baseline. Right 
panel shows classification results with 95% precision on class A.

Presentation Usage:
Use this figure to explain the system design (panel a) and demonstrate 
performance improvements (panels b-c). Consider splitting into 2 slides:
one for architecture, one for results.

Importance: 0.95
```

This is MUCH better than:
```
Extracted: image_page3_fragment_12.png
Description: A blue rectangle
Importance: 0.3
```

---

## 🎯 Benefits

1. **Accuracy**: Figures are described as they actually appear
2. **Completeness**: Multi-panel figures stay together
3. **Context**: Gemini understands what figures *mean*
4. **Reliability**: No dependency on fragile PDF parsing
5. **Quality**: Better slide generation decisions

---

## ⚠️ Considerations

### Pros
- ✅ Much better quality
- ✅ Handles complex academic figures
- ✅ Understands visual context
- ✅ No extraction artifacts

### Cons
- ⏱️ Slower (Gemini API calls for each PDF)
- 💰 Costs API tokens
- 🌐 Requires internet connection
- 📦 Larger payload (full PDF upload)

### When to Use PDF Extraction
- Simple documents with actual raster images (photos)
- Need offline processing
- Cost is a major concern
- Figures are already high-quality PNGs in the PDF

### When to Use Gemini Analysis (Recommended)
- Academic papers with vector graphics ✅
- Multi-panel figures ✅
- Figures with text overlays ✅
- Tables ✅
- Diagrams ✅
- **Default for this use case** ✅

---

## 🔧 Technical Details

### How It Works

1. **PDF Upload**: Upload entire PDF to Gemini
   ```python
   file_ref = client.files.upload(path=str(pdf_path))
   ```

2. **Structured Analysis**: Request figure descriptions with schema
   ```python
   figures = client.generate_structured_output(
       prompt="Analyze all figures...",
       response_schema=PaperFiguresSchema,
       pdf_path=pdf_path
   )
   ```

3. **Validation**: Pydantic ensures correct structure
   ```python
   # Guaranteed to have these fields
   for fig in figures.figures:
       page = fig.page_number  # int
       desc = fig.visual_description  # str
       importance = fig.importance  # float 0-1
   ```

4. **Integration**: Pass to presentation planner
   ```python
   plan = planner.create_plan(
       paper_analysis,
       pdf_metadata,
       saved_images=[],  # Empty - no extraction
       figure_descriptions  # From Gemini
   )
   ```

---

## 📚 Files Modified

1. **`src/utils/models.py`**
   - Added `FigureDescriptionSchema`
   - Added `PaperFiguresSchema`

2. **`src/llm/document_analyzer.py`**
   - Added `analyze_figures_from_pdf()` method
   - Added `_get_figure_analysis_prompt()` helper

3. **`src/llm/gemini_client.py`**
   - Updated `generate_structured_output()` to accept `pdf_path`

4. **`src/llm/prompts/figure_analysis.txt`**
   - New prompt for figure analysis

5. **`src/llm/prompts/paper_analysis.txt`**
   - Updated to mention figures and tables

6. **`scripts/generate_slides.py`**
   - Added `--extract-images` flag (opt-in)
   - Added `--use-gemini-figures` (default true)
   - Updated workflow to use Gemini analysis
   - Made PDF extraction optional

---

## 🎉 Result

**The system now uses Gemini's vision capabilities to analyze figures directly from PDFs, avoiding the fragmentation problem of PDF image extraction entirely.**

This is the **recommended approach** for academic papers and is now the **default behavior**.

---

**Status**: ✅ **IMPLEMENTED AND TESTED**  
**Recommendation**: ✅ **USE GEMINI ANALYSIS (DEFAULT)**  
**Fallback**: ⚠️ **PDF Extraction available with `--extract-images` flag**
