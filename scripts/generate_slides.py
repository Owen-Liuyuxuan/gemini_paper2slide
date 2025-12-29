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


def save_checkpoint(output_dir: Path, step: str, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Save checkpoint for recovery.
    
    Args:
        output_dir: Output directory
        step: Checkpoint step name
        data: Optional data to save with checkpoint
    """
    checkpoint_dir = output_dir / ".checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint_data = {
        "step": step,
        "timestamp": datetime.now().isoformat(),
        "data": data or {}
    }
    
    checkpoint_file = checkpoint_dir / f"{step}.json"
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint_data, f, indent=2, default=str)


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
        
        save_checkpoint(output_path, "paper_analysis", {
            "summary": paper_analysis.summary,
        })
        
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
        
        save_checkpoint(output_path, "presentation_planning", {
            "total_slides": presentation_plan.total_slides
        })
        
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
    
    save_checkpoint(output_path, "slide_generation", {
        "slides_generated": len(slides)
    })

    # STEP 5: Save outputs
    logger.info("\n" + "="*80)
    logger.info("STEP 5: Saving outputs...")
    logger.info("="*80)
    
    try:
        image_saver = ImageSaver(output_dir)
        image_saver.save_slides(slides)
        logger.info(f"✓ Saved {len(slides)} slide images")
        
        #image_saver.save_metadata(presentation_plan, slides)
        logger.info("✓ Saved presentation metadata")
        
        save_checkpoint(output_path, "complete", {
            "total_slides": len(slides),
            "output_directory": str(output_path)
        })
        
    except Exception as e:
        logger.error(f"Saving outputs failed: {e}", exc_info=True)
        raise
    
    # Success!
    logger.info("\n" + "="*80)
    logger.info("✓ SLIDE GENERATION COMPLETE!")
    logger.info("="*80)
    logger.info(f"Successfully generated {len(slides)} slides")
    logger.info(f"Output directory: {output_path.absolute()}")
    logger.info(f"Slides: {output_path / 'slide_*.png'}")
    logger.info(f"Metadata: {output_path / 'presentation_metadata.json'}")
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
