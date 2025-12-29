# Refactoring Plan: PDF-to-Slides System

**Date**: 2025-12-27  
**Priority**: Fix critical bugs that prevent system from working

---

## Critical Fixes (Must Do First)

### 1. Fix Gemini Image Generation API ❌ BROKEN

**File**: `src/llm/gemini_client.py`  
**Lines**: 278-439  
**Problem**: `ImageConfig` doesn't have `reference_images` parameter

**Solution**: Since Gemini's image generation API doesn't support reference images for style consistency in `ImageConfig`, we need to use a different approach:

**Option A: Image-to-Image Editing** (RECOMMENDED)
```python
# For visual consistency, use the previous slide as base_image
# Then apply new content via editing
def generate_slide_with_consistency(self, prompt: str, previous_slide_image: bytes):
    return self.gemini_client.generate_image(
        prompt=prompt,
        base_image=previous_slide_image,  # Pass as content for editing
        aspect_ratio="16:9"
    )
```

**Option B: Enhanced Text Prompts**
```python
# Extract style from first slide, describe it, use in prompts
def generate_slide_with_style(self, prompt: str, style_description: str):
    enhanced_prompt = f"""
{prompt}

**Style Requirements:**
{style_description}

Ensure visual consistency with previous slides.
"""
    return self.gemini_client.generate_image(
        prompt=enhanced_prompt,
        aspect_ratio="16:9"
    )
```

---

### 2. Implement Proper Slide Generation Workflow ❌ MISSING

**File**: `src/presentation/slide_generator.py`  
**Lines**: 70-106  
**Problem**: All slides generated the same way, no special handling for title/reference slides

**Solution**: Implement 3-stage workflow

```python
def generate_slide_sequence(self, plan: PresentationPlan, pdf_images: List[ExtractedImage]) -> List[GeneratedSlide]:
    logger.info("Starting sequential slide generation")
    generated_slides = []
    
    # STAGE 1: Generate title slide (special)
    if len(plan.slides) > 0 and plan.slides[0].type == SlideType.TITLE:
        title_info = {
            "title": plan.metadata.title,
            "authors": plan.metadata.authors,
            "theme": plan.analysis.visual_theme
        }
        title_slide = self.image_generator.generate_title_slide(title_info)
        generated_slides.append(title_slide)
        logger.info("Generated title slide")
    
    # STAGE 2: Generate second slide using title for consistency
    if len(plan.slides) > 1:
        slide_content = plan.slides[1]
        # Use image-to-image with title slide as base
        second_slide = self.image_generator.generate_content_slide(
            content=slide_content,
            references=[generated_slides[0]],  # Only title slide
            pdf_images=[]
        )
        generated_slides.append(second_slide)
        logger.info("Generated reference slide")
    
    # STAGE 3: Generate remaining slides with both references
    for slide_content in plan.slides[2:]:
        related_images_paths = [
            str(pdf_images[i].file_path) 
            for i in slide_content.related_pdf_images 
            if i < len(pdf_images) and pdf_images[i].file_path
        ]
        
        slide = self.image_generator.generate_content_slide(
            content=slide_content,
            references=generated_slides[:2],  # First 2 slides as references
            pdf_images=related_images_paths
        )
        generated_slides.append(slide)
        logger.info(f"Generated slide {slide_content.index}")
    
    return generated_slides
```

---

### 3. Replace Dummy Parsing with Structured Output ❌ DUMMY CODE

**File**: `src/llm/document_analyzer.py`  
**Lines**: 135-300  
**Problem**: String matching instead of structured output

**Solution**: Define Pydantic schemas and use structured output

```python
# Add to models.py
class KeyPointSchema(BaseModel):
    title: str
    content: str
    importance: float = Field(ge=0.0, le=1.0)
    section: str
    related_figure_pages: List[int] = Field(default_factory=list)

class PaperAnalysisSchema(BaseModel):
    summary: str
    research_question: str
    methodology: str
    key_contributions: List[str]
    key_points: List[KeyPointSchema]
    recommended_slide_count: int = Field(ge=5, le=20)
    visual_theme: str

# In document_analyzer.py
def analyze_paper(self, pdf_path: Path) -> PaperAnalysis:
    logger.info(f"Analyzing paper: {pdf_path}")
    
    prompt = self._get_prompt('paper_analysis')
    enriched_prompt = f"""{prompt}

Please analyze the document and provide a comprehensive, structured analysis.
Focus on:
1. Clear research question and motivation
2. Methodology and approach details
3. Key contributions (3-5 items)
4. Important points for presentation (5-10 items)
5. Recommended number of slides
6. Suggested visual theme

Output should be in valid JSON format matching the schema.
"""
    
    # Read PDF for context
    pdf_data = pdf_path.read_bytes()
    
    # First get the analysis text
    analysis_text = self.gemini_client.analyze_document(
        pdf_data=pdf_data,
        prompt=enriched_prompt
    )
    
    # Then parse into structured format
    structure_prompt = f"""
Based on the following paper analysis, extract structured information:

{analysis_text}

Provide the information in valid JSON format.
"""
    
    analysis_schema = self.gemini_client.generate_structured_output(
        prompt=structure_prompt,
        response_schema=PaperAnalysisSchema
    )
    
    # Convert to PaperAnalysis model
    key_points = [
        KeyPoint(
            title=kp.title,
            content=kp.content,
            importance=kp.importance,
            section=kp.section,
            related_figures=kp.related_figure_pages
        )
        for kp in analysis_schema.key_points
    ]
    
    return PaperAnalysis(
        summary=analysis_schema.summary,
        research_question=analysis_schema.research_question,
        methodology=analysis_schema.methodology,
        key_contributions=analysis_schema.key_contributions,
        key_points=key_points,
        important_figures=[],  # Will be filled later
        recommended_slide_count=analysis_schema.recommended_slide_count,
        visual_theme=analysis_schema.visual_theme
    )
```

---

### 4. Fix Presentation Planner to Use Gemini Output ❌ IGNORING OUTPUT

**File**: `src/presentation/planner.py`  
**Lines**: 56-78, 220-294  
**Problem**: Generates plan but doesn't use it

**Solution**: Use structured output directly

```python
# Add to models.py
class SlideSpec(BaseModel):
    index: int
    type: str
    title: str
    key_points: List[str]
    visual_suggestions: str
    related_figure_pages: List[int] = Field(default_factory=list)

class PresentationPlanSchema(BaseModel):
    slide_count: int = Field(ge=5, le=20)
    slides: List[SlideSpec]
    style_description: str

# In planner.py
def create_plan(
    self, 
    paper_analysis: PaperAnalysis, 
    pdf_metadata: PDFMetadata, 
    pdf_images: List[ExtractedImage]
) -> PresentationPlan:
    logger.info("Creating presentation plan")
    
    prompt = f"""
Create a comprehensive presentation plan for the following academic paper:

**Paper Information:**
- Title: {pdf_metadata.title}
- Authors: {', '.join(pdf_metadata.authors)}
- Page Count: {pdf_metadata.page_count}

**Analysis:**
- Research Question: {paper_analysis.research_question}
- Methodology: {paper_analysis.methodology}
- Key Contributions: {', '.join(paper_analysis.key_contributions)}
- Visual Theme: {paper_analysis.visual_theme}

**Key Points to Cover:**
{self._format_key_points(paper_analysis.key_points)}

**Available Figures:** {len(pdf_images)} figures extracted from PDF

Please create a detailed presentation plan with:
1. Optimal number of slides (recommended: {paper_analysis.recommended_slide_count})
2. For each slide:
   - Type (title, agenda, content, figure, conclusion)
   - Title
   - Key points to cover (3-5 bullet points)
   - Visual suggestions
   - Which PDF figures to include (if any, by page number)

The presentation should flow logically and tell a compelling story.
Provide the plan in JSON format.
"""
    
    plan_schema = self.gemini_client.generate_structured_output(
        prompt=prompt,
        response_schema=PresentationPlanSchema
    )
    
    # Convert to SlideContent objects
    slides = []
    for slide_spec in plan_schema.slides:
        # Map string type to enum
        slide_type = self._parse_slide_type(slide_spec.type)
        
        # Map page numbers to image indices
        related_images = []
        for page_num in slide_spec.related_figure_pages:
            for idx, img in enumerate(pdf_images):
                if img.page_num == page_num:
                    related_images.append(idx)
                    break
        
        slide = SlideContent(
            index=slide_spec.index,
            type=slide_type,
            title=slide_spec.title,
            main_points=slide_spec.key_points,
            visual_elements=slide_spec.visual_suggestions,
            related_pdf_images=related_images,
            notes=f"Generated by AI planner"
        )
        slides.append(slide)
    
    presentation_plan = PresentationPlan(
        metadata=pdf_metadata,
        analysis=paper_analysis,
        slides=slides,
        style_guidelines={"description": plan_schema.style_description},
        total_slides=len(slides)
    )
    
    logger.info(f"Created presentation plan with {len(slides)} slides")
    return presentation_plan
```

---

## Medium Priority Fixes

### 5. Add Image Description Integration

**File**: `src/llm/document_analyzer.py`  
**New Method**:

```python
def describe_pdf_images(self, pdf_images: List[ExtractedImage]) -> Dict[int, str]:
    """
    Generate descriptions for important PDF images.
    
    Args:
        pdf_images: List of extracted images
    
    Returns:
        Dictionary mapping image index to description
    """
    logger.info(f"Generating descriptions for {len(pdf_images)} images")
    
    descriptions = {}
    important_images = [
        (idx, img) for idx, img in enumerate(pdf_images)
        if img.quality_score >= 0.6  # Only high-quality images
    ]
    
    for idx, img in important_images[:10]:  # Limit to top 10
        try:
            if img.file_path:
                description = self.gemini_client.describe_image(
                    image_path=img.file_path,
                    prompt="""
Describe this figure from an academic paper:
1. What type of visualization is it? (graph, diagram, photo, etc.)
2. What are the main elements shown?
3. What does it illustrate or demonstrate?
4. Key insights or findings shown
"""
                )
                descriptions[idx] = description
                logger.debug(f"Described image {idx}: {description[:100]}...")
        except Exception as e:
            logger.warning(f"Failed to describe image {idx}: {e}")
            continue
    
    return descriptions
```

**Update main workflow** (`scripts/generate_slides.py`):
```python
# After Step 2: Analyzing paper
image_descriptions = doc_analyzer.describe_pdf_images(saved_images)

# Pass to planner
presentation_plan = presentation_planner.create_plan(
    paper_analysis, pdf_metadata, saved_images, image_descriptions
)
```

---

### 6. Add Error Recovery and Checkpoints

**File**: `scripts/generate_slides.py`

```python
import json
from pathlib import Path

def save_checkpoint(output_dir: Path, step: str, data: Any):
    """Save checkpoint for recovery."""
    checkpoint_dir = output_dir / ".checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    
    checkpoint_file = checkpoint_dir / f"{step}.json"
    with open(checkpoint_file, 'w') as f:
        json.dump({"step": step, "timestamp": datetime.now().isoformat()}, f)
    
    logger.info(f"Saved checkpoint: {step}")

def load_checkpoint(output_dir: Path) -> Optional[str]:
    """Load last checkpoint if exists."""
    checkpoint_dir = output_dir / ".checkpoints"
    if not checkpoint_dir.exists():
        return None
    
    checkpoints = sorted(checkpoint_dir.glob("*.json"))
    if checkpoints:
        with open(checkpoints[-1]) as f:
            data = json.load(f)
        return data.get("step")
    return None

def main(pdf_path: str, output_dir: str, use_cache: bool = True, resume: bool = False):
    """Main workflow with error recovery."""
    logger = setup_logger(__name__)
    output_path = Path(output_dir)
    
    try:
        # Check for resume
        last_step = None
        if resume:
            last_step = load_checkpoint(output_path)
            if last_step:
                logger.info(f"Resuming from step: {last_step}")
        
        # Step 1: PDF Extraction
        if not last_step or last_step == "start":
            logger.info("Step 1: Extracting PDF content...")
            pdf_reader = PDFReader()
            pdf_text = pdf_reader.extract_text(Path(pdf_path))
            pdf_metadata = pdf_reader.extract_metadata(Path(pdf_path))
            
            image_extractor = ImageExtractor()
            pdf_images = image_extractor.extract_images(Path(pdf_path))
            filtered_images = image_extractor.filter_images(pdf_images)
            saved_images = image_extractor.save_images(
                filtered_images, 
                output_path / "extracted_images"
            )
            save_checkpoint(output_path, "pdf_extraction", None)
        else:
            # Load from cache
            logger.info("Loading PDF extraction from checkpoint...")
            # ... load saved data ...
        
        # Step 2: Paper Analysis
        if not last_step or last_step in ["start", "pdf_extraction"]:
            logger.info("Step 2: Analyzing paper...")
            gemini_client = GeminiClient()
            doc_analyzer = DocumentAnalyzer(gemini_client)
            
            cache_key = f"analysis_{Path(pdf_path).stem}"
            cache = CacheManager() if use_cache else None
            
            if cache and cache.exists(cache_key):
                paper_analysis = cache.get(cache_key)
            else:
                paper_analysis = doc_analyzer.analyze_paper(Path(pdf_path))
                if cache:
                    cache.set(cache_key, paper_analysis)
            
            save_checkpoint(output_path, "paper_analysis", None)
        
        # Step 3: Presentation Planning
        if not last_step or last_step in ["start", "pdf_extraction", "paper_analysis"]:
            logger.info("Step 3: Creating presentation plan...")
            presentation_planner = PresentationPlanner(gemini_client)
            presentation_plan = presentation_planner.create_plan(
                paper_analysis, pdf_metadata, saved_images
            )
            save_checkpoint(output_path, "presentation_planning", None)
        
        # Step 4: Slide Generation
        if not last_step or last_step != "slide_generation_complete":
            logger.info("Step 4: Generating slides...")
            style_manager = StyleManager()
            image_generator = ImageGenerator(gemini_client)
            slide_generator = SlideGenerator(image_generator, style_manager)
            
            slides = slide_generator.generate_slide_sequence(
                presentation_plan, saved_images
            )
            save_checkpoint(output_path, "slide_generation", None)
        
        # Step 5: Save Output
        logger.info("Step 5: Saving outputs...")
        image_saver = ImageSaver(output_dir)
        image_saver.save_slides(slides)
        image_saver.save_metadata(presentation_plan, slides)
        save_checkpoint(output_path, "slide_generation_complete", None)
        
        logger.info(f"Successfully generated {len(slides)} slides in {output_dir}")
        
    except KeyboardInterrupt:
        logger.warning("Generation interrupted by user")
        save_checkpoint(output_path, "interrupted", None)
        raise
    except Exception as e:
        logger.error(f"Slide generation failed: {e}", exc_info=True)
        save_checkpoint(output_path, "failed", None)
        raise
```

---

## Testing Plan

### Unit Tests

1. **Test Gemini Client**
   ```python
   def test_image_generation():
       client = GeminiClient()
       image = client.generate_image(prompt="Test slide")
       assert len(image) > 0
   ```

2. **Test PDF Processing**
   ```python
   def test_pdf_extraction():
       reader = PDFReader()
       content = reader.extract_text(Path("test.pdf"))
       assert content["page_count"] > 0
   ```

3. **Test Structured Output**
   ```python
   def test_structured_analysis():
       client = GeminiClient()
       result = client.generate_structured_output(
           prompt="Analyze: Machine learning paper",
           response_schema=PaperAnalysisSchema
       )
       assert result.summary
       assert len(result.key_contributions) > 0
   ```

### Integration Tests

1. **End-to-End Test**
   ```bash
   python scripts/generate_slides.py --pdf test_paper.pdf --output test_output/
   ```

2. **Resume Test**
   ```bash
   # Kill after step 2
   python scripts/generate_slides.py --pdf test.pdf --output test_output/
   # Resume
   python scripts/generate_slides.py --pdf test.pdf --output test_output/ --resume
   ```

---

## Completion Checklist

### Phase 1: Critical Fixes
- [ ] Fix image generation API (remove `reference_images` from `ImageConfig`)
- [ ] Implement proper 3-stage slide generation workflow
- [ ] Replace string parsing with structured output in analyzer
- [ ] Fix planner to use Gemini output correctly
- [ ] Test all critical components

### Phase 2: Quality Improvements
- [ ] Add image description integration
- [ ] Add error recovery with checkpoints
- [ ] Add comprehensive logging
- [ ] Test with real papers

### Phase 3: Polish
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Update documentation
- [ ] Performance optimization

---

## Estimated Timeline

- **Phase 1 (Critical)**: 2-3 days
- **Phase 2 (Quality)**: 2-3 days
- **Phase 3 (Polish)**: 1-2 days

**Total**: 5-8 days of focused development

---

## Success Criteria

✅ System runs without crashes
✅ Generates slides with visual consistency
✅ Uses structured output for all AI interactions
✅ Handles errors gracefully
✅ Can resume after interruption
✅ Produces high-quality presentations
