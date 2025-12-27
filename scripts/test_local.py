#!/usr/bin/env python3
"""
Local testing script for the paper-to-slides system.

This script tests the core functionality without actually processing a PDF.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.llm.gemini_client import GeminiClient
from src.utils.config_loader import get_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_config_loading():
    """Test configuration loading."""
    logger.info("Testing configuration loading...")
    
    config = get_config("gemini")
    logger.info(f"Loaded Gemini config: {config}")
    
    if config and config.get("api_key"):
        logger.info("✓ API key loaded successfully")
    else:
        logger.warning("⚠ API key not found - please set GOOGLE_API_KEY environment variable")
    
    return True


def test_gemini_client():
    """Test Gemini client initialization."""
    logger.info("Testing Gemini client initialization...")
    
    try:
        # This will fail without an API key, but should initialize properly
        config = get_config("gemini")
        api_key = config.get("api_key")
        
        if not api_key:
            logger.warning("⚠ Cannot test Gemini client without API key")
            return False
        
        client = GeminiClient()
        logger.info("✓ Gemini client initialized successfully")
        
        # Test text generation (optional, only if API key is available)
        try:
            response = client.generate_text(
                prompt="Say hello in exactly one word",
                max_tokens=10
            )
            logger.info(f"✓ Text generation test: {response}")
        except Exception as e:
            logger.warning(f"⚠ Text generation failed (expected if API is not configured): {e}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize Gemini client: {e}")
        return False


def test_data_models():
    """Test data models."""
    logger.info("Testing data models...")
    
    try:
        from src.utils.models import (
            PDFMetadata, 
            PaperAnalysis, 
            KeyPoint, 
            SlideContent, 
            GeneratedSlide, 
            SlideType
        )
        
        # Test creating a simple PDFMetadata object
        metadata = PDFMetadata(
            title="Test Paper",
            authors=["Author 1", "Author 2"],
            page_count=10,
            file_path="test.pdf"
        )
        logger.info(f"✓ PDFMetadata created: {metadata.title}")
        
        # Test creating a simple KeyPoint
        keypoint = KeyPoint(
            title="Test Key Point",
            content="This is a test key point",
            importance=0.8,
            section="test"
        )
        logger.info(f"✓ KeyPoint created: {keypoint.title}")
        
        # Test creating a simple SlideContent
        slide_content = SlideContent(
            index=0,
            type=SlideType.TITLE,
            title="Test Slide",
            main_points=["Point 1", "Point 2"],
            visual_elements="Test visual elements",
            related_pdf_images=[]
        )
        logger.info(f"✓ SlideContent created: {slide_content.title}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to test data models: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("Starting local tests for paper-to-slides system...")
    
    tests = [
        ("Configuration Loading", test_config_loading),
        ("Data Models", test_data_models),
        ("Gemini Client", test_gemini_client),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✓ {test_name} PASSED")
            else:
                logger.info(f"✗ {test_name} FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n--- Test Summary ---")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.info(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())