#!/usr/bin/env python3
"""
Main script for generating presentation slides from academic papers.

Usage:
    python scripts/generate_slides.py --pdf path/to/paper.pdf --output output_dir/
    python scripts/generate_slides.py --pdf paper.pdf --output output/ --no-cache
    python scripts/generate_slides.py --pdf paper.pdf --output output/ --resume
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.llm.document_analyzer import DocumentAnalyzer
from src.llm.gemini_client import GeminiClient
from src.output.image_saver import ImageSaver
from src.presentation.planner import PresentationPlanner
from src.presentation.slide_generator import SlideGenerator
from src.presentation.style_manager import StyleManager
from src.utils.cache_manager import CacheManager
from src.utils.logger import setup_logger
from src.utils.models import PaperAnalysisSchema, PresentationPlan


def serialize_for_checkpoint(obj: Any) -> Any:
    """
    Serialize objects to JSON-serializable format for checkpoints.
    
    Handles Pydantic models, dicts, lists, and basic types.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON-serializable representation
    """
    if hasattr(obj, 'model_dump'):
        # Pydantic v2 model
        return obj.model_dump()
    elif hasattr(obj, 'dict'):
        # Pydantic v1 model
        return obj.dict()
    elif isinstance(obj, dict):
        return {k: serialize_for_checkpoint(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_checkpoint(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, Path):
        return str(obj)
    elif hasattr(obj, '__dict__'):
        return serialize_for_checkpoint(obj.__dict__)
    else:
        return str(obj)


def save_checkpoint(
    output_dir: Path, 
    step: str, 
    data: Optional[Dict[str, Any]] = None,
    paper_analysis: Optional[PaperAnalysisSchema] = None,
    presentation_plan: Optional[PresentationPlan] = None
) -> None:
    """
    Save comprehensive checkpoint with all text results in readable format.
    
    Saves both JSON (for programmatic access) and human-readable text files.
    
    Args:
        output_dir: Output directory
        step: Checkpoint step name
        data: Optional additional data to save
        paper_analysis: Paper analysis results (if available)
        presentation_plan: Presentation plan (if available)
    """
    checkpoint_dir = output_dir / ".checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # Build comprehensive checkpoint data
    checkpoint_data = {
        "step": step,
        "timestamp": datetime.now().isoformat(),
        "data": data or {}
    }
    
    # Add paper analysis if provided
    if paper_analysis:
        checkpoint_data["paper_analysis"] = serialize_for_checkpoint(paper_analysis)
    
    # Add presentation plan if provided
    if presentation_plan:
        checkpoint_data["presentation_plan"] = {
            "analysis": serialize_for_checkpoint(presentation_plan.analysis),
            "total_slides": presentation_plan.total_slides,
            "style_guidelines": serialize_for_checkpoint(presentation_plan.style_guidelines),
            "slides": [
                {
                    "index": slide.index,
                    "type": slide.type.value,
                    "title": slide.title,
                    "main_points": slide.main_points,
                    "visual_elements": slide.visual_elements
                }
                for slide in presentation_plan.slides
            ]
        }
    
    # Save JSON checkpoint
    checkpoint_file = checkpoint_dir / f"{step}.json"
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False, default=str)
    
    # Save human-readable text checkpoint
    text_file = checkpoint_dir / f"{step}.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(f"Checkpoint: {step}\n")
        f.write(f"Timestamp: {checkpoint_data['timestamp']}\n")
        f.write("=" * 80 + "\n\n")
        
        if paper_analysis:
            f.write("PAPER ANALYSIS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Summary:\n{paper_analysis.summary}\n\n")
            f.write(f"Core Philosophy:\n{paper_analysis.core_philosophy}\n\n")
            f.write(f"Mathematical Formulation:\n{paper_analysis.mathematical_formulation}\n\n")
            f.write(f"Methodology:\n{paper_analysis.methodology}\n\n")
            f.write(f"Key Contributions:\n")
            for i, contrib in enumerate(paper_analysis.key_contributions, 1):
                f.write(f"  {i}. {contrib}\n")
            f.write(f"\nRecommended Slide Count: {paper_analysis.recommended_slide_count}\n")
            f.write(f"Visual Theme: {paper_analysis.visual_theme}\n\n")
            f.write("=" * 80 + "\n\n")
        
        if presentation_plan:
            f.write("PRESENTATION PLAN\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Slides: {presentation_plan.total_slides}\n")
            f.write(f"Style Guidelines: {presentation_plan.style_guidelines.get('description', 'N/A')}\n\n")
            
            f.write("SLIDE SPECIFICATIONS\n")
            f.write("-" * 80 + "\n")
            for slide in presentation_plan.slides:
                f.write(f"\nSlide {slide.index}: {slide.title} ({slide.type.value})\n")
                f.write(f"Main Points:\n")
                for i, point in enumerate(slide.main_points, 1):
                    f.write(f"  {i}. {point}\n")
                f.write(f"Visual Elements: {slide.visual_elements}\n")
                f.write("-" * 40 + "\n")
            f.write("\n" + "=" * 80 + "\n\n")
        
        if data:
            f.write("ADDITIONAL DATA\n")
            f.write("-" * 80 + "\n")
            for key, value in data.items():
                f.write(f"{key}: {value}\n")
            f.write("\n" + "=" * 80 + "\n")


def load_last_checkpoint(output_dir: Path) -> Optional[str]:
    """
    Load last successful checkpoint if exists.
    
    Args:
        output_dir: Output directory
    
    Returns:
        Last completed step name or None
    """
    checkpoint_dir = output_dir / ".checkpoints"
    if not checkpoint_dir.exists():
        return None
    
    checkpoints = sorted(checkpoint_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if checkpoints:
        with open(checkpoints[-1]) as f:
            data = json.load(f)
        return data.get("step")
    return None


def main(
    pdf_path: str, 
    output_dir: str, 
    use_cache: bool = True, 
    resume: bool = False,
) -> None:
    """
    Main workflow for generating presentation slides.
    
    Args:
        pdf_path: Path to input PDF file
        output_dir: Directory for output slides
        use_cache: Whether to use cached intermediate results
        resume: Whether to resume from last checkpoint
        use_gemini_figures: Whether to use Gemini's direct figure analysis (recommended)
        resume: Whether to resume from last checkpoint
        describe_images: Whether to generate descriptions for PDF images
    """
    logger = setup_logger(__name__)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("="*80)
    logger.info(f"Starting slide generation for: {pdf_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Cache: {'enabled' if use_cache else 'disabled'}")
    logger.info(f"Resume: {'yes' if resume else 'no'}")
    logger.info("="*80)
    
    # Check for resume
    last_step = None
    if resume:
        last_step = load_last_checkpoint(output_path)
        if last_step:
            logger.info(f"Resuming from checkpoint: {last_step}")
    
    # Validate PDF exists
    pdf_path_obj = Path(pdf_path)
    if not pdf_path_obj.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Initialize cache if enabled
    cache = CacheManager() if use_cache else None
    # STEP 1: Analyze paper with Gemini
    logger.info("\n" + "="*80)
    logger.info("STEP 1: Analyzing paper with Gemini...")
    logger.info("="*80)
    
    try:
        gemini_client = GeminiClient()
        doc_analyzer = DocumentAnalyzer(gemini_client)
        
        cache_key = f"analysis_{pdf_path_obj.stem}"
        
        if cache and cache.exists(cache_key):
            paper_analysis = cache.get(cache_key)
            logger.info("✓ Retrieved analysis from cache")
        else:
            paper_analysis = doc_analyzer.analyze_paper(pdf_path_obj)
            if cache:
                cache.set(cache_key, paper_analysis)
            logger.info("✓ Paper analysis complete")
        
        logger.info(f"  - Core Idea: {paper_analysis.core_philosophy[:100]}...")
        logger.info(f"  - Recommended Slides: {paper_analysis.recommended_slide_count}")
        
        save_checkpoint(
            output_path, 
            "paper_analysis", 
            data={"recommended_slide_count": paper_analysis.recommended_slide_count},
            paper_analysis=paper_analysis
        )
        logger.info(f"✓ Checkpoint saved: paper_analysis (JSON + readable text)")
        
    except Exception as e:
        logger.error(f"Paper analysis failed: {e}", exc_info=True)
        raise
    
    # STEP 2: Create presentation plan
    logger.info("\n" + "="*80)
    logger.info("STEP 2: Creating presentation plan...")
    logger.info("="*80)
    
    try:
        presentation_planner = PresentationPlanner(gemini_client)
        presentation_plan = presentation_planner.create_plan(
            paper_analysis, 
            pdf_path_obj
        )
        
        logger.info(f"✓ Created plan with {presentation_plan.total_slides} slides")
        for slide in presentation_plan.slides[:3]:  # Show first 3
            logger.info(f"  - Slide {slide.index}: {slide.title} ({slide.type.value})")
        if presentation_plan.total_slides > 3:
            logger.info(f"  ... and {presentation_plan.total_slides - 3} more slides")
        
        save_checkpoint(
            output_path, 
            "presentation_planning",
            data={"total_slides": presentation_plan.total_slides},
            paper_analysis=paper_analysis,
            presentation_plan=presentation_plan
        )
        logger.info(f"✓ Checkpoint saved: presentation_planning (JSON + readable text)")
        
    except Exception as e:
        logger.error(f"Presentation planning failed: {e}", exc_info=True)
        raise
    
    # STEP 4: Generate slides
    logger.info("\n" + "="*80)
    logger.info("STEP 4: Generating slides...")
    logger.info("="*80)
    logger.info("This may take several minutes depending on the number of slides...")
    
    slide_generator = SlideGenerator(gemini_client)
    print(presentation_plan)
    slides = slide_generator.generate_slide_sequence(
        presentation_plan, 
        pdf_path_obj
    )
    
    logger.info(f"✓ Generated {len(slides)} slides")
    
    # Save slide content information in checkpoint
    slide_info = []
    for i, (slide_img, slide_spec) in enumerate(zip(slides, presentation_plan.slides)):
        slide_info.append({
            "index": slide_spec.index,
            "type": slide_spec.type.value,
            "title": slide_spec.title,
            "main_points": slide_spec.main_points,
            "visual_elements": slide_spec.visual_elements
        })
    
    save_checkpoint(
        output_path, 
        "slide_generation",
        data={
            "slides_generated": len(slides),
            "slide_info": slide_info
        },
        paper_analysis=paper_analysis,
        presentation_plan=presentation_plan
    )
    logger.info(f"✓ Checkpoint saved: slide_generation (JSON + readable text)")

    # STEP 5: Save outputs
    logger.info("\n" + "="*80)
    logger.info("STEP 5: Saving outputs...")
    logger.info("="*80)
    
    try:
        image_saver = ImageSaver(output_dir)
        slide_paths = image_saver.save_slides(slides)
        logger.info(f"✓ Saved {len(slides)} slide images")
        
        # Merge slides into PDF
        pdf_path = image_saver.merge_slides_to_pdf(slide_paths=slide_paths)
        logger.info(f"✓ Merged slides into PDF: {pdf_path.name}")
        
        #image_saver.save_metadata(presentation_plan, slides)
        logger.info("✓ Saved presentation metadata")
        
        save_checkpoint(
            output_path, 
            "complete",
            data={
                "total_slides": len(slides),
                "output_directory": str(output_path),
                "slide_files": [f"slide_{i:02d}.png" for i in range(len(slides))],
                "pdf_file": pdf_path.name
            },
            paper_analysis=paper_analysis,
            presentation_plan=presentation_plan
        )
        logger.info(f"✓ Final checkpoint saved: complete (JSON + readable text)")
        
    except Exception as e:
        logger.error(f"Saving outputs failed: {e}", exc_info=True)
        raise
    
    # Success!
    logger.info("\n" + "="*80)
    logger.info("✓ SLIDE GENERATION COMPLETE!")
    logger.info("="*80)
    logger.info(f"Successfully generated {len(slides)} slides")
    logger.info(f"Output directory: {output_path.absolute()}")
    logger.info(f"Individual slides: {output_path / 'slide_*.png'}")
    logger.info(f"Combined PDF: {output_path / 'presentation.pdf'}")
    logger.info(f"Metadata: {output_path / 'presentation_metadata.json'}")
    logger.info(f"Checkpoints: {output_path / '.checkpoints'}")
    logger.info("="*80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate presentation slides from academic papers using Gemini AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (recommended - uses Gemini figure analysis)
  python scripts/generate_slides.py --pdf paper.pdf --output output/
  
  # Disable caching
  python scripts/generate_slides.py --pdf paper.pdf --output output/ --no-cache
  
  # Resume after interruption
  python scripts/generate_slides.py --pdf paper.pdf --output output/ --resume
  
  # Use old PDF image extraction method (not recommended)
  python scripts/generate_slides.py --pdf paper.pdf --output output/ --extract-images
"""
    )
    
    parser.add_argument(
        "--pdf", 
        required=True, 
        help="Path to input PDF file"
    )
    parser.add_argument(
        "--output", 
        required=True, 
        help="Output directory for generated slides"
    )
    parser.add_argument(
        "--no-cache", 
        action="store_true", 
        help="Disable caching of intermediate results"
    )
    parser.add_argument(
        "--resume", 
        action="store_true",
        help="Resume from last checkpoint if available"
    )
    parser.add_argument(
        "--extract-images",
        action="store_true",
        default=False,
        help="Extract images from PDF (not recommended for academic papers with vector graphics)"
    )
    parser.add_argument(
        "--use-gemini-figures",
        action="store_true",
        default=True,
        help="Use Gemini's direct PDF figure analysis instead of extraction (recommended, default)"
    )
    
    args = parser.parse_args()
    
    main(
        args.pdf, 
        args.output, 
        use_cache=not args.no_cache,
        resume=args.resume,
    )
