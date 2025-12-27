#!/usr/bin/env python3
"""
Main script for generating presentation slides from academic papers.

Usage:
    python scripts/generate_slides.py --pdf path/to/paper.pdf --output output_dir/
"""

import argparse
import logging
from pathlib import Path
from typing import Optional

from src.llm.document_analyzer import DocumentAnalyzer
from src.llm.gemini_client import GeminiClient
from src.llm.image_generator import ImageGenerator
from src.output.image_saver import ImageSaver
from src.pdf.image_extractor import ImageExtractor
from src.pdf.reader import PDFReader
from src.presentation.planner import PresentationPlanner
from src.presentation.slide_generator import SlideGenerator
from src.presentation.style_manager import StyleManager
from src.utils.cache_manager import CacheManager
from src.utils.logger import setup_logger


def main(pdf_path: str, output_dir: str, use_cache: bool = True):
    """
    Main workflow for generating presentation slides.
    
    Args:
        pdf_path: Path to input PDF file
        output_dir: Directory for output slides
        use_cache: Whether to use cached intermediate results
    """
    logger = setup_logger(__name__)
    logger.info(f"Starting slide generation for {pdf_path}")
    
    # Initialize components
    pdf_reader = PDFReader()
    image_extractor = ImageExtractor()
    gemini_client = GeminiClient()
    doc_analyzer = DocumentAnalyzer(gemini_client)
    style_manager = StyleManager()
    image_generator = ImageGenerator(gemini_client)
    presentation_planner = PresentationPlanner(gemini_client)
    slide_generator = SlideGenerator(image_generator, style_manager)
    image_saver = ImageSaver(output_dir)
    cache = CacheManager() if use_cache else None
    
    # Step 1: Extract PDF content
    logger.info("Step 1: Extracting PDF content...")
    pdf_text = pdf_reader.extract_text(Path(pdf_path))
    pdf_metadata = pdf_reader.extract_metadata(Path(pdf_path))
    pdf_images = image_extractor.extract_images(Path(pdf_path))
    filtered_images = image_extractor.filter_images(pdf_images)
    saved_images = image_extractor.save_images(filtered_images, Path(output_dir) / "extracted_images")
    
    # Step 2: Analyzing paper with Gemini
    logger.info("Step 2: Analyzing paper with Gemini...")
    cache_key = f"analysis_{Path(pdf_path).stem}"
    
    if cache and cache.exists(cache_key):
        paper_analysis = cache.get(cache_key)
        logger.info("Retrieved analysis from cache")
    else:
        paper_analysis = doc_analyzer.analyze_paper(Path(pdf_path))
        if cache:
            cache.set(cache_key, paper_analysis)
            logger.info("Cached analysis result")
    
    # Step 3: Create presentation plan
    logger.info("Step 3: Creating presentation plan...")
    presentation_plan = presentation_planner.create_plan(
        paper_analysis, pdf_metadata, saved_images
    )
    
    # Step 4: Generate slides
    logger.info("Step 4: Generating slides...")
    slides = slide_generator.generate_slide_sequence(
        presentation_plan, saved_images
    )
    
    # Step 5: Save outputs
    logger.info("Step 5: Saving outputs...")
    image_saver.save_slides(slides)
    image_saver.save_metadata(presentation_plan, slides)
    
    logger.info(f"Successfully generated {len(slides)} slides in {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate presentation slides from academic papers"
    )
    parser.add_argument(
        "--pdf", required=True, help="Path to input PDF file"
    )
    parser.add_argument(
        "--output", required=True, help="Output directory for slides"
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Disable caching"
    )
    
    args = parser.parse_args()
    main(args.pdf, args.output, use_cache=not args.no_cache)
