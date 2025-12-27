I'll create a comprehensive, detailed coding plan with specific implementation instructions suitable for coding agents.

# Detailed Implementation Plan for PDF-to-Slides System

## Project Setup and Configuration

### Task 1.1: Initialize Project Structure
**Priority: P0 | Estimated Time: 30 minutes**

```bash
# Create directory structure
mkdir -p paper_to_slides/{config,src/{pdf,llm/prompts,presentation,output,utils},scripts,tests,docs/examples}
cd paper_to_slides

# Initialize git repository
git init
git remote add origin <your-repo-url>

# Create Python package files
touch src/__init__.py
touch src/pdf/__init__.py
touch src/llm/__init__.py
touch src/presentation/__init__.py
touch src/output/__init__.py
touch src/utils/__init__.py
```

**Acceptance Criteria:**
- All directories created
- `__init__.py` files in all package directories
- Git repository initialized

### Task 1.2: Create Configuration Files
**Priority: P0 | Estimated Time: 20 minutes**

**File: `pyproject.toml`**
```toml
[build-system]
requires = ["setuptools>=68.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "paper-to-slides"
version = "0.1.0"
description = "Generate presentation slides from academic papers using Gemini AI"
authors = [
    {name = "Owen", email = "your.email@example.com"}
]
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}

dependencies = [
    "google-generativeai>=0.8.0",
    "PyMuPDF>=1.24.0",
    "Pillow>=10.0.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "tenacity>=8.2.0",
    "loguru>=0.7.0",
    "aiofiles>=23.0.0",
    "httpx>=0.25.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "pre-commit>=3.5.0",
]

[tool.black]
line-length = 100
target-version = ['py310', 'py311']
include = '\.pyi?$'

[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --cov=src --cov-report=html --cov-report=term"
```

**File: `config/config.json`**
```json
{
  "gemini": {
    "model_text": "gemini-2.0-flash-exp",
    "model_image": "imagen-3.0-generate-001",
    "temperature": 0.7,
    "max_retries": 3,
    "retry_delay": 2,
    "timeout": 120
  },
  "pdf": {
    "max_pages": 50,
    "image_quality_threshold": 0.5,
    "min_image_size": [100, 100],
    "max_image_size": [4096, 4096],
    "supported_formats": ["png", "jpg", "jpeg"]
  },
  "presentation": {
    "default_slide_count": 10,
    "max_slides": 15,
    "min_slides": 5,
    "image_format": "png",
    "image_size": [1920, 1080],
    "aspect_ratio": "16:9"
  },
  "cache": {
    "enabled": true,
    "ttl_hours": 24,
    "cache_dir": ".cache"
  },
  "logging": {
    "level": "INFO",
    "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    "log_dir": "logs"
  }
}
```

**File: `.env.example`**
```bash
# Google Gemini API Configuration
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: Google Cloud Project (if using Vertex AI)
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Cache Configuration
CACHE_ENABLED=true
CACHE_DIR=.cache

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs

# Output Configuration
OUTPUT_DIR=output
```

**File: `.gitignore`**
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env

# Cache
.cache/
*.cache

# Logs
logs/
*.log

# Output
output/
*.png
*.jpg

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db
```

**Acceptance Criteria:**
- All configuration files created
- Valid JSON syntax in config files
- `.env.example` provides clear template

---

## Phase 1: Core Data Models and Utilities

### Task 2.1: Define Data Models
**Priority: P0 | Estimated Time: 1 hour**

**File: `src/utils/models.py`**
```python
"""
Core data models for the paper-to-slides system.

This module defines Pydantic models for type safety and validation
across the entire application.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ImageFormat(str, Enum):
    """Supported image formats."""
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"


class SlideType(str, Enum):
    """Types of slides in a presentation."""
    TITLE = "title"
    AGENDA = "agenda"
    CONTENT = "content"
    FIGURE = "figure"
    CONCLUSION = "conclusion"


class ExtractedImage(BaseModel):
    """
    Represents an image extracted from a PDF.
    
    Attributes:
        page_num: Page number where image was found (0-indexed)
        index: Index of image on the page
        data: Raw image bytes
        format: Image format (png, jpeg, etc.)
        width: Image width in pixels
        height: Image height in pixels
        file_path: Optional path where image is saved
        quality_score: Computed quality score (0-1)
    """
    page_num: int = Field(..., ge=0, description="Page number (0-indexed)")
    index: int = Field(..., ge=0, description="Image index on page")
    data: bytes = Field(..., description="Raw image data")
    format: ImageFormat = Field(..., description="Image format")
    width: int = Field(..., gt=0, description="Image width in pixels")
    height: int = Field(..., gt=0, description="Image height in pixels")
    file_path: Optional[Path] = Field(None, description="Saved file path")
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Quality score")
    
    class Config:
        arbitrary_types_allowed = True
    
    @field_validator('data')
    @classmethod
    def validate_data_not_empty(cls, v: bytes) -> bytes:
        """Ensure image data is not empty."""
        if len(v) == 0:
            raise ValueError("Image data cannot be empty")
        return v
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio (width/height)."""
        return self.width / self.height if self.height > 0 else 0.0
    
    @property
    def size_kb(self) -> float:
        """Get image size in kilobytes."""
        return len(self.data) / 1024


class PDFMetadata(BaseModel):
    """
    Metadata extracted from PDF document.
    
    Attributes:
        title: Document title
        authors: List of authors
        abstract: Paper abstract
        keywords: List of keywords
        page_count: Number of pages
        creation_date: Document creation date
        file_path: Path to PDF file
    """
    title: str = Field(..., min_length=1, description="Document title")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    abstract: Optional[str] = Field(None, description="Paper abstract")
    keywords: List[str] = Field(default_factory=list, description="Keywords")
    page_count: int = Field(..., gt=0, description="Number of pages")
    creation_date: Optional[datetime] = Field(None, description="Creation date")
    file_path: Path = Field(..., description="Path to PDF file")
    
    class Config:
        arbitrary_types_allowed = True


class KeyPoint(BaseModel):
    """
    A key point extracted from the paper.
    
    Attributes:
        title: Short title for the key point
        content: Detailed content
        importance: Importance score (0-1)
        section: Section where this point appears
        related_figures: Indices of related figures
    """
    title: str = Field(..., min_length=1, description="Key point title")
    content: str = Field(..., min_length=1, description="Detailed content")
    importance: float = Field(..., ge=0.0, le=1.0, description="Importance score")
    section: str = Field(..., description="Source section")
    related_figures: List[int] = Field(default_factory=list, description="Related figure indices")


class PaperAnalysis(BaseModel):
    """
    Comprehensive analysis of the paper.
    
    Attributes:
        summary: Overall summary
        research_question: Main research question
        methodology: Research methodology description
        key_contributions: List of key contributions
        key_points: Detailed key points
        important_figures: Indices of important figures
        recommended_slide_count: Recommended number of slides
        visual_theme: Suggested visual theme
    """
    summary: str = Field(..., min_length=1, description="Overall summary")
    research_question: str = Field(..., description="Main research question")
    methodology: str = Field(..., description="Methodology description")
    key_contributions: List[str] = Field(..., min_items=1, description="Key contributions")
    key_points: List[KeyPoint] = Field(..., min_items=1, description="Detailed key points")
    important_figures: List[int] = Field(default_factory=list, description="Important figure indices")
    recommended_slide_count: int = Field(..., ge=5, le=20, description="Recommended slides")
    visual_theme: str = Field(..., description="Suggested visual theme")


class SlideContent(BaseModel):
    """
    Content specification for a single slide.
    
    Attributes:
        index: Slide index in presentation
        type: Type of slide
        title: Slide title
        main_points: Main content points
        visual_elements: Description of visual elements
        related_pdf_images: Indices of related PDF images
        notes: Speaker notes or additional context
    """
    index: int = Field(..., ge=0, description="Slide index")
    type: SlideType = Field(..., description="Slide type")
    title: str = Field(..., min_length=1, description="Slide title")
    main_points: List[str] = Field(..., description="Main content points")
    visual_elements: str = Field(..., description="Visual elements description")
    related_pdf_images: List[int] = Field(default_factory=list, description="Related PDF images")
    notes: Optional[str] = Field(None, description="Speaker notes")


class PresentationPlan(BaseModel):
    """
    Complete plan for the presentation.
    
    Attributes:
        metadata: PDF metadata
        analysis: Paper analysis
        slides: List of slide content specifications
        style_guidelines: Visual style guidelines
        total_slides: Total number of slides
    """
    metadata: PDFMetadata = Field(..., description="PDF metadata")
    analysis: PaperAnalysis = Field(..., description="Paper analysis")
    slides: List[SlideContent] = Field(..., min_items=1, description="Slide specifications")
    style_guidelines: Dict[str, Any] = Field(..., description="Style guidelines")
    total_slides: int = Field(..., gt=0, description="Total slide count")
    
    @field_validator('total_slides')
    @classmethod
    def validate_total_slides(cls, v: int, info: Any) -> int:
        """Ensure total_slides matches length of slides list."""
        if 'slides' in info.data and len(info.data['slides']) != v:
            raise ValueError("total_slides must match length of slides list")
        return v


class GeneratedSlide(BaseModel):
    """
    A generated slide image with metadata.
    
    Attributes:
        index: Slide index
        type: Slide type
        image: Raw image bytes
        prompt: Generation prompt used
        file_path: Path where image is saved
        generation_time: Time taken to generate
        content: Original content specification
    """
    index: int = Field(..., ge=0, description="Slide index")
    type: SlideType = Field(..., description="Slide type")
    image: bytes = Field(..., description="Generated image data")
    prompt: str = Field(..., description="Generation prompt")
    file_path: Optional[Path] = Field(None, description="Saved file path")
    generation_time: float = Field(..., ge=0.0, description="Generation time in seconds")
    content: SlideContent = Field(..., description="Content specification")
    
    class Config:
        arbitrary_types_allowed = True
    
    @property
    def size_mb(self) -> float:
        """Get image size in megabytes."""
        return len(self.image) / (1024 * 1024)


class GenerationConfig(BaseModel):
    """
    Configuration for image generation.
    
    Attributes:
        aspect_ratio: Image aspect ratio
        quality: Quality setting
        style: Visual style
        safety_filter_level: Safety filter level
        number_of_images: Number of images to generate
    """
    aspect_ratio: str = Field("16:9", description="Aspect ratio")
    quality: str = Field("high", description="Quality setting")
    style: str = Field("professional", description="Visual style")
    safety_filter_level: str = Field("block_some", description="Safety filter")
    number_of_images: int = Field(1, ge=1, le=4, description="Number of images")
```

**Acceptance Criteria:**
- All models use Pydantic v2 syntax
- Type hints are complete and accurate
- Validators ensure data integrity
- Docstrings follow Google style
- Models are immutable where appropriate

### Task 2.2: Implement Logger Utility
**Priority: P0 | Estimated Time: 30 minutes**

**File: `src/utils/logger.py`**
```python
"""
Logging utilities for the paper-to-slides system.

Provides structured logging with file and console output using loguru.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from src.utils.config_loader import load_config


def setup_logger(
    name: Optional[str] = None,
    log_level: Optional[str] = None,
    log_dir: Optional[Path] = None
) -> "logger":
    """
    Set up the application logger with console and file handlers.
    
    Args:
        name: Logger name (used for filtering)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logger("pdf_processor", "DEBUG")
        >>> logger.info("Processing started")
    """
    # Load configuration
    config = load_config()
    log_config = config.get("logging", {})
    
    # Use provided values or fall back to config
    log_level = log_level or log_config.get("level", "INFO")
    log_dir = log_dir or Path(log_config.get("log_dir", "logs"))
    log_format = log_config.get(
        "format",
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler for all logs
    logger.add(
        log_dir / "paper_to_slides.log",
        format=log_format,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Add separate error log
    logger.add(
        log_dir / "errors.log",
        format=log_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Add context filter if name provided
    if name:
        logger = logger.bind(name=name)
    
    logger.info(f"Logger initialized with level: {log_level}")
    return logger


def get_logger(name: str) -> "logger":
    """
    Get a logger instance with a specific name.
    
    Args:
        name: Logger name for identification
    
    Returns:
        Logger instance bound to the given name
    
    Example:
        >>> logger = get_logger("image_generator")
        >>> logger.debug("Starting image generation")
    """
    return logger.bind(name=name)
```

**Acceptance Criteria:**
- Logger uses loguru for structured logging
- Console and file outputs configured
- Log rotation and retention implemented
- Error logs separated
- Context binding works correctly

### Task 2.3: Implement Configuration Loader
**Priority: P0 | Estimated Time: 30 minutes**

**File: `src/utils/config_loader.py`**
```python
"""
Configuration management for the paper-to-slides system.

Handles loading and merging configuration from JSON files and environment variables.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv


class ConfigLoader:
    """
    Singleton configuration loader.
    
    Loads configuration from JSON files and environment variables,
    with environment variables taking precedence.
    """
    
    _instance: Optional['ConfigLoader'] = None
    _config: Optional[Dict[str, Any]] = None
    
    def __new__(cls) -> 'ConfigLoader':
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize configuration loader."""
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from files and environment."""
        # Load environment variables
        load_dotenv()
        
        # Determine config directory
        config_dir = Path(__file__).parent.parent.parent / "config"
        
        # Load main config
        config_path = config_dir / "config.json"
        with open(config_path, 'r') as f:
            self._config = json.load(f)
        
        # Override with environment variables
        self._apply_env_overrides()
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        if self._config is None:
            return
        
        # Gemini API key
        if api_key := os.getenv("GOOGLE_API_KEY"):
            self._config.setdefault("gemini", {})["api_key"] = api_key
        
        # Cache settings
        if cache_enabled := os.getenv("CACHE_ENABLED"):
            self._config.setdefault("cache", {})["enabled"] = cache_enabled.lower() == "true"
        
        if cache_dir := os.getenv("CACHE_DIR"):
            self._config.setdefault("cache", {})["cache_dir"] = cache_dir
        
        # Logging settings
        if log_level := os.getenv("LOG_LEVEL"):
            self._config.setdefault("logging", {})["level"] = log_level
        
        if log_dir := os.getenv("LOG_DIR"):
            self._config.setdefault("logging", {})["log_dir"] = log_dir
        
        # Output directory
        if output_dir := os.getenv("OUTPUT_DIR"):
            self._config["output_dir"] = output_dir
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., "gemini.model_text")
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        
        Example:
            >>> config = ConfigLoader()
            >>> model = config.get("gemini.model_text")
        """
        if self._config is None:
            return default
        
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get entire configuration dictionary.
        
        Returns:
            Complete configuration dictionary
        """
        return self._config.copy() if self._config else {}
    
    def reload(self) -> None:
        """Reload configuration from files."""
        self._config = None
        self._load_config()


# Global configuration loader instance
_config_loader = ConfigLoader()


def load_config() -> Dict[str, Any]:
    """
    Load and return the complete configuration.
    
    Returns:
        Configuration dictionary
    
    Example:
        >>> config = load_config()
        >>> print(config["gemini"]["model_text"])
    """
    return _config_loader.get_all()


def get_config(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value.
    
    Args:
        key: Configuration key (supports dot notation)
        default: Default value if key not found
    
    Returns:
        Configuration value or default
    
    Example:
        >>> api_key = get_config("gemini.api_key")
    """
    return _config_loader.get(key, default)


def reload_config() -> None:
    """
    Reload configuration from files.
    
    Useful for testing or when configuration files change.
    """
    _config_loader.reload()
```

**Acceptance Criteria:**
- Singleton pattern implemented correctly
- JSON configuration loaded
- Environment variables override config
- Dot notation supported for nested keys
- Thread-safe implementation

### Task 2.4: Implement Cache Manager
**Priority: P1 | Estimated Time: 45 minutes**

**File: `src/utils/cache_manager.py`**
```python
"""
Cache management for expensive operations.

Provides disk-based caching for API responses and intermediate results.
"""

import hashlib
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from src.utils.config_loader import get_config
from src.utils.logger import get_logger

logger = get_logger("cache_manager")


class CacheManager:
    """
    Disk-based cache manager with TTL support.
    
    Caches Python objects using pickle and provides automatic expiration.
    
    Attributes:
        cache_dir: Directory for cache files
        ttl_hours: Time-to-live in hours
        enabled: Whether caching is enabled
    """
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl_hours: Optional[int] = None,
        enabled: Optional[bool] = None
    ) -> None:
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Cache directory (default from config)
            ttl_hours: Time-to-live in hours (default from config)
            enabled: Enable/disable caching (default from config)
        """
        cache_config = get_config("cache", {})
        
        self.enabled = enabled if enabled is not None else cache_config.get("enabled", True)
        self.cache_dir = cache_dir or Path(cache_config.get("cache_dir", ".cache"))
        self.ttl_hours = ttl_hours or cache_config.get("ttl_hours", 24)
        
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache initialized at {self.cache_dir} with TTL={self.ttl_hours}h")
    
    def _get_cache_path(self, key: str) -> Path:
        """
        Get cache file path for a given key.
        
        Args:
            key: Cache key
        
        Returns:
            Path to cache file
        """
        # Hash the key to create a valid filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _is_expired(self, cache_path: Path) -> bool:
        """
        Check if cache file is expired.
        
        Args:
            cache_path: Path to cache file
        
        Returns:
            True if expired, False otherwise
        """
        if not cache_path.exists():
            return True
        
        # Check file modification time
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        expiry_time = mtime + timedelta(hours=self.ttl_hours)
        
        return datetime.now() > expiry_time
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        
        Example:
            >>> cache = CacheManager()
            >>> result = cache.get("paper_analysis_xyz")
        """
        if not self.enabled:
            return None
        
        cache_path = self._get_cache_path(key)
        
        if self._is_expired(cache_path):
            logger.debug(f"Cache miss or expired for key: {key}")
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                value = pickle.load(f)
            logger.debug(f"Cache hit for key: {key}")
            return value
        except Exception as e:
            logger.warning(f"Failed to load cache for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be picklable)
        
        Example:
            >>> cache = CacheManager()
            >>> cache.set("paper_analysis_xyz", analysis_result)
        """
        if not self.enabled:
            return
        
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
            logger.debug(f"Cached value for key: {key}")
        except Exception as e:
            logger.warning(f"Failed to cache value for key {key}: {e}")
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache and is not expired.
        
        Args:
            key: Cache key
        
        Returns:
            True if exists and not expired, False otherwise
        """
        if not self.enabled:
            return False
        
        cache_path = self._get_cache_path(key)
        return cache_path.exists() and not self._is_expired(cache_path)
    
    def delete(self, key: str) -> None:
        """
        Delete cached value.
        
        Args:
            key: Cache key
        """
        if not self.enabled:
            return
        
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"Deleted cache for key: {key}")
    
    def clear(self) -> None:
        """
        Clear all cached values.
        """
        if not self.enabled:
            return
        
        count = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
            count += 1
        
        logger.info(f"Cleared {count} cache files")
    
    def clear_expired(self) -> None:
        """
        Remove expired cache files.
        """
        if not self.enabled:
            return
        
        count = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            if self._is_expired(cache_file):
                cache_file.unlink()
                count += 1
        
        logger.info(f"Removed {count} expired cache files")
```

**Acceptance Criteria:**
- Pickle-based serialization works
- TTL expiration implemented correctly
- Cache directory created automatically
- Thread-safe file operations
- Proper error handling

---

## Phase 2: PDF Processing Module

### Task 3.1: Implement PDF Reader
**Priority: P0 | Estimated Time: 1.5 hours**

**File: `src/pdf/reader.py`**
```python
"""
PDF text extraction and metadata parsing.

Uses PyMuPDF (fitz) for efficient PDF processing.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import fitz  # PyMuPDF

from src.utils.logger import get_logger
from src.utils.models import PDFMetadata

logger = get_logger("pdf_reader")


class PDFReader:
    """
    Extract text and metadata from PDF documents.
    
    Uses PyMuPDF for high-performance PDF processing with support
    for text extraction, metadata parsing, and document structure analysis.
    """
    
    def __init__(self) -> None:
        """Initialize PDF reader."""
        logger.info("PDFReader initialized")
    
    def extract_text(self, pdf_path: Path) -> Dict[str, any]:
        """
        Extract text content from PDF.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary containing:
                - full_text: Complete document text
                - pages: List of page texts
                - page_count: Number of pages
                - toc: Table of contents if available
        
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is encrypted or corrupted
        
        Example:
            >>> reader = PDFReader()
            >>> content = reader.extract_text(Path("paper.pdf"))
            >>> print(content["full_text"][:100])
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting text from {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            
            if doc.is_encrypted:
                raise ValueError(f"PDF is encrypted: {pdf_path}")
            
            # Extract text from all pages
            pages = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                pages.append({
                    "page_num": page_num,
                    "text": text,
                    "word_count": len(text.split())
                })
            
            # Combine all text
            full_text = "\n\n".join(page["text"] for page in pages)
            
            # Extract table of contents
            toc = doc.get_toc()
            
            doc.close()
            
            result = {
                "full_text": full_text,
                "pages": pages,
                "page_count": len(pages),
                "toc": toc,
                "word_count": len(full_text.split())
            }
            
            logger.info(
                f"Extracted {result['page_count']} pages, "
                f"{result['word_count']} words from {pdf_path.name}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            raise
    
    def extract_metadata(self, pdf_path: Path) -> PDFMetadata:
        """
        Extract metadata from PDF.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            PDFMetadata object with document information
        
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If required metadata is missing
        
        Example:
            >>> reader = PDFReader()
            >>> metadata = reader.extract_metadata(Path("paper.pdf"))
            >>> print(metadata.title)
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting metadata from {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            meta = doc.metadata
            
            # Extract title (fallback to filename if not in metadata)
            title = meta.get("title", "") or pdf_path.stem
            
            # Extract authors
            authors_str = meta.get("author", "")
            authors = [a.strip() for a in authors_str.split(",") if a.strip()]
            
            # Extract keywords
            keywords_str = meta.get("keywords", "")
            keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
            
            # Extract creation date
            creation_date = None
            if date_str := meta.get("creationDate"):
                try:
                    # PyMuPDF date format: D:YYYYMMDDHHmmSSOHH'mm'
                    if date_str.startswith("D:"):
                        date_str = date_str[2:16]  # Extract YYYYMMDDHHmmSS
                        creation_date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
                except Exception as e:
                    logger.warning(f"Failed to parse creation date: {e}")
            
            # Extract abstract (try to find it in first page)
            abstract = self._extract_abstract(doc)
            
            page_count = len(doc)
            doc.close()
            
            metadata = PDFMetadata(
                title=title,
                authors=authors,
                abstract=abstract,
                keywords=keywords,
                page_count=page_count,
                creation_date=creation_date,
                file_path=pdf_path
            )
            
            logger.info(f"Extracted metadata: {title} by {', '.join(authors)}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {pdf_path}: {e}")
            raise
    
    def _extract_abstract(self, doc: fitz.Document) -> Optional[str]:
        """
        Attempt to extract abstract from first few pages.
        
        Args:
            doc: Opened PyMuPDF document
        
        Returns:
            Abstract text or None if not found
        """
        # Search first 3 pages for abstract
        for page_num in range(min(3, len(doc))):
            page = doc[page_num]
            text = page.get_text("text")
            
            # Look for "Abstract" section
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if "abstract" in line.lower() and len(line) < 50:
                    # Found abstract header, collect following lines
                    abstract_lines = []
                    for j in range(i + 1, min(i + 20, len(lines))):
                        if lines[j].strip():
                            # Stop at next section header
                            if any(keyword in lines[j].lower() 
                                   for keyword in ["introduction", "1.", "keywords"]):
                                break
                            abstract_lines.append(lines[j].strip())
                    
                    if abstract_lines:
                        return " ".join(abstract_lines)
        
        return None
    
    def get_page_count(self, pdf_path: Path) -> int:
        """
        Get number of pages in PDF.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Number of pages
        
        Example:
            >>> reader = PDFReader()
            >>> count = reader.get_page_count(Path("paper.pdf"))
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        
        return count
```

**Acceptance Criteria:**
- PyMuPDF correctly extracts text
- Metadata parsing handles missing fields
- Abstract extraction works for common formats
- Error handling for encrypted/corrupted PDFs
- Comprehensive logging

### Task 3.2: Implement Image Extractor
**Priority: P0 | Estimated Time: 2 hours**

**File: `src/pdf/image_extractor.py`**
```python
"""
Extract and process images from PDF documents.

Uses PyMuPDF for image extraction with quality filtering and preprocessing.
"""

from io import BytesIO
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF
from PIL import Image

from src.utils.config_loader import get_config
from src.utils.logger import get_logger
from src.utils.models import ExtractedImage, ImageFormat

logger = get_logger("image_extractor")


class ImageExtractor:
    """
    Extract and filter images from PDF documents.
    
    Extracts all images from PDF pages, filters by quality and size,
    and prepares them for use in slide generation.
    
    Attributes:
        min_size: Minimum image dimensions (width, height)
        max_size: Maximum image dimensions
        quality_threshold: Minimum quality score (0-1)
    """
    
    def __init__(
        self,
        min_size: Optional[tuple[int, int]] = None,
        max_size: Optional[tuple[int, int]] = None,
        quality_threshold: Optional[float] = None
    ) -> None:
        """
        Initialize image extractor.
        
        Args:
            min_size: Minimum (width, height) in pixels
            max_size: Maximum (width, height) in pixels
            quality_threshold: Minimum quality score (0-1)
        """
        pdf_config = get_config("pdf", {})
        
        self.min_size = min_size or tuple(pdf_config.get("min_image_size", [100, 100]))
        self.max_size = max_size or tuple(pdf_config.get("max_image_size", [4096, 4096]))
        self.quality_threshold = quality_threshold or pdf_config.get("image_quality_threshold", 0.5)
        
        logger.info(
            f"ImageExtractor initialized: min_size={self.min_size}, "
            f"max_size={self.max_size}, quality_threshold={self.quality_threshold}"
        )
    
    def extract_images(self, pdf_path: Path) -> List[ExtractedImage]:
        """
        Extract all images from PDF.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            List of ExtractedImage objects
        
        Raises:
            FileNotFoundError: If PDF file doesn't exist
        
        Example:
            >>> extractor = ImageExtractor()
            >>> images = extractor.extract_images(Path("paper.pdf"))
            >>> print(f"Found {len(images)} images")
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting images from {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            extracted_images = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)
                
                logger.debug(f"Page {page_num}: found {len(image_list)} images")
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        
                        # Get image data
                        image_data = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Convert extension to ImageFormat
                        if image_ext == "png":
                            img_format = ImageFormat.PNG
                        elif image_ext in ["jpeg", "jpg"]:
                            img_format = ImageFormat.JPEG
                        else:
                            # Convert unsupported formats to PNG
                            img_format = ImageFormat.PNG
                            image_data = self._convert_to_png(image_data)
                        
                        # Get dimensions
                        width = base_image.get("width", 0)
                        height = base_image.get("height", 0)
                        
                        # Calculate quality score
                        quality_score = self._calculate_quality_score(
                            image_data, width, height
                        )
                        
                        extracted_image = ExtractedImage(
                            page_num=page_num,
                            index=img_index,
                            data=image_data,
                            format=img_format,
                            width=width,
                            height=height,
                            quality_score=quality_score
                        )
                        
                        extracted_images.append(extracted_image)
                        
                    except Exception as e:
                        logger.warning(
                            f"Failed to extract image {img_index} from page {page_num}: {e}"
                        )
                        continue
            
            doc.close()
            
            logger.info(f"Extracted {len(extracted_images)} images from {pdf_path.name}")
            
            return extracted_images
            
        except Exception as e:
            logger.error(f"Failed to extract images from {pdf_path}: {e}")
            raise
    
    def filter_images(self, images: List[ExtractedImage]) -> List[ExtractedImage]:
        """
        Filter images by size and quality.
        
        Args:
            images: List of extracted images
        
        Returns:
            Filtered list of images
        
        Example:
            >>> extractor = ImageExtractor()
            >>> all_images = extractor.extract_images(Path("paper.pdf"))
            >>> good_images = extractor.filter_images(all_images)
        """
        logger.info(f"Filtering {len(images)} images")
        
        filtered = []
        
        for img in images:
            # Check size constraints
            if img.width < self.min_size[0] or img.height < self.min_size[1]:
                logger.debug(
                    f"Skipping image (too small): {img.width}x{img.height} "
                    f"on page {img.page_num}"
                )
                continue
            
            if img.width > self.max_size[0] or img.height > self.max_size[1]:
                logger.debug(
                    f"Skipping image (too large): {img.width}x{img.height} "
                    f"on page {img.page_num}"
                )
                continue
            
            # Check quality
            if img.quality_score < self.quality_threshold:
                logger.debug(
                    f"Skipping image (low quality): score={img.quality_score:.2f} "
                    f"on page {img.page_num}"
                )
                continue
            
            filtered.append(img)
        
        logger.info(f"Filtered to {len(filtered)} high-quality images")
        
        return filtered
    
    def save_images(
        self,
        images: List[ExtractedImage],
        output_dir: Path,
        prefix: str = "extracted"
    ) -> List[ExtractedImage]:
        """
        Save extracted images to disk.
        
        Args:
            images: List of images to save
            output_dir: Output directory
            prefix: Filename prefix
        
        Returns:
            List of images with updated file_path
        
        Example:
            >>> extractor = ImageExtractor()
            >>> images = extractor.extract_images(Path("paper.pdf"))
            >>> saved = extractor.save_images(images, Path("output/images"))
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving {len(images)} images to {output_dir}")
        
        saved_images = []
        
        for img in images:
            filename = f"{prefix}_p{img.page_num}_i{img.index}.{img.format.value}"
            file_path = output_dir / filename
            
            try:
                with open(file_path, 'wb') as f:
                    f.write(img.data)
                
                # Update image with file path
                img.file_path = file_path
                saved_images.append(img)
                
                logger.debug(f"Saved image to {file_path}")
                
            except Exception as e:
                logger.warning(f"Failed to save image {filename}: {e}")
                continue
        
        logger.info(f"Successfully saved {len(saved_images)} images")
        
        return saved_images
    
    def _convert_to_png(self, image_data: bytes) -> bytes:
        """
        Convert image data to PNG format.
        
        Args:
            image_data: Raw image bytes
        
        Returns:
            PNG image bytes
        """
        try:
            img = Image.open(BytesIO(image_data))
            output = BytesIO()
            img.save(output, format='PNG')
            return output.getvalue()
        except Exception as e:
            logger.warning(f"Failed to convert image to PNG: {e}")
            return image_data
    
    def _calculate_quality_score(
        self,
        image_data: bytes,
        width: int,
        height: int
    ) -> float:
        """
        Calculate image quality score.
        
        Considers:
        - Resolution (higher is better)
        - Aspect ratio (closer to common ratios is better)
        - File size relative to dimensions
        
        Args:
            image_data: Raw image bytes
            width: Image width
            height: Image height
        
        Returns:
            Quality score between 0 and 1
        """
        try:
            # Resolution score (normalize to 0-1)
            resolution = width * height
            resolution_score = min(resolution / (1920 * 1080), 1.0)
            
            # Aspect ratio score (prefer 16:9, 4:3, 1:1)
            aspect_ratio = width / height if height > 0 else 0
            common_ratios = [16/9, 4/3, 1.0, 3/4, 9/16]
            aspect_score = max(
                1.0 - abs(aspect_ratio - ratio) / ratio
                for ratio in common_ratios
            )
            
            # File size score (bytes per pixel)
            bytes_per_pixel = len(image_data) / resolution if resolution > 0 else 0
            # Expect 1-4 bytes per pixel for good quality
            size_score = 1.0 if 1 <= bytes_per_pixel <= 4 else 0.5
            
            # Weighted average
            quality_score = (
                0.4 * resolution_score +
                0.3 * aspect_score +
                0.3 * size_score
            )
            
            return min(max(quality_score, 0.0), 1.0)
            
        except Exception as e:
            logger.warning(f"Failed to calculate quality score: {e}")
            return 0.5
```

**Acceptance Criteria:**
- Extracts all images from PDF pages
- Quality scoring algorithm implemented
- Size filtering works correctly
- Image format conversion handles edge cases
- Saved images have correct paths

---

## Phase 3: LLM Integration Module

### Task 4.1: Implement Gemini Client
**Priority: P0 | Estimated Time: 2 hours**

**File: `src/llm/gemini_client.py`**
```python
"""
Google Gemini API client with retry logic and error handling.

Provides unified interface for text generation, document analysis,
and image generation using Gemini models.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import google.generativeai as genai
from google.generativeai.types import GenerationConfig, HarmBlockThreshold, HarmCategory
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.utils.config_loader import get_config
from src.utils.logger import get_logger

logger = get_logger("gemini_client")


class GeminiClient:
    """
    Client for Google Gemini API.
    
    Handles text generation, document analysis, and image generation
    with automatic retry logic and error handling.
    
    Attributes:
        api_key: Google API key
        model_text: Text generation model name
        model_image: Image generation model name
        temperature: Generation temperature
        max_retries: Maximum retry attempts
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_text: Optional[str] = None,
        model_image: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: Optional[int] = None
    ) -> None:
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google API key (default from config)
            model_text: Text model name (default from config)
            model_image: Image model name (default from config)
            temperature: Generation temperature (default from config)
            max_retries: Max retry attempts (default from config)
        
        Raises:
            ValueError: If API key is not provided
        """
        gemini_config = get_config("gemini", {})
        
        self.api_key = api_key or gemini_config.get("api_key")
        if not self.api_key:
            raise ValueError("Google API key not provided")
        
        self.model_text = model_text or gemini_config.get("model_text", "gemini-2.0-flash-exp")
        self.model_image = model_image or gemini_config.get("model_image", "imagen-3.0-generate-001")
        self.temperature = temperature or gemini_config.get("temperature", 0.7)
        self.max_retries = max_retries or gemini_config.get("max_retries", 3)
        
        # Configure API
        genai.configure(api_key=self.api_key)
        
        # Initialize models
        self._text_model = genai.GenerativeModel(self.model_text)
        self._image_model = genai.ImageGenerationModel(self.model_image)
        
        logger.info(
            f"GeminiClient initialized: text_model={self.model_text}, "
            f"image_model={self.model_image}"
        )
    
    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate_text(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text using Gemini.
        
        Args:
            prompt: Input prompt
            temperature: Generation temperature (overrides default)
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated text
        
        Raises:
            Exception: If generation fails after retries
        
        Example:
            >>> client = GeminiClient()
            >>> response = client.generate_text("Explain quantum computing")
        """
        logger.debug(f"Generating text with prompt length: {len(prompt)}")
        
        generation_config = GenerationConfig(
            temperature=temperature or self.temperature,
            max_output_tokens=max_tokens or 8192,
        )
        
        try:
            response = self._text_model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            text = response.text
            logger.debug(f"Generated {len(text)} characters")
            
            return text
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise
    
    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def analyze_document(
        self,
        pdf_path: Optional[Path] = None,
        pdf_data: Optional[bytes] = None,
        prompt: str = "Analyze this document",
        mime_type: str = "application/pdf"
    ) -> str:
        """
        Analyze PDF document using Gemini's multimodal capabilities.
        
        Args:
            pdf_path: Path to PDF file
            pdf_data: Raw PDF bytes (alternative to pdf_path)
            prompt: Analysis prompt
            mime_type: MIME type of document
        
        Returns:
            Analysis text
        
        Raises:
            ValueError: If neither pdf_path nor pdf_data provided
            Exception: If analysis fails
        
        Example:
            >>> client = GeminiClient()
            >>> analysis = client.analyze_document(
            ...     pdf_path=Path("paper.pdf"),
            ...     prompt="Summarize the key contributions"
            ... )
        """
        if pdf_path is None and pdf_data is None:
            raise ValueError("Either pdf_path or pdf_data must be provided")
        
        logger.info("Analyzing document with Gemini")
        
        try:
            # Load PDF data if path provided
            if pdf_path and pdf_data is None:
                with open(pdf_path, 'rb') as f:
                    pdf_data = f.read()
            
            # Upload file to Gemini
            uploaded_file = genai.upload_file(
                data=pdf_data,
                mime_type=mime_type
            )
            
            logger.debug(f"Uploaded file: {uploaded_file.name}")
            
            # Generate analysis
            response = self._text_model.generate_content(
                [prompt, uploaded_file],
                generation_config=GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=8192,
                )
            )
            
            analysis = response.text
            logger.info(f"Document analysis complete: {len(analysis)} characters")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            raise
    
    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=20),
        reraise=True
    )
    def generate_image(
        self,
        prompt: str,
        reference_images: Optional[List[Union[Path, bytes]]] = None,
        aspect_ratio: str = "16:9",
        number_of_images: int = 1
    ) -> bytes:
        """
        Generate image using Gemini's Imagen model.
        
        Args:
            prompt: Image generation prompt
            reference_images: List of reference images (paths or bytes)
            aspect_ratio: Image aspect ratio (16:9, 4:3, 1:1, etc.)
            number_of_images: Number of images to generate
        
        Returns:
            Generated image bytes (PNG format)
        
        Raises:
            Exception: If generation fails
        
        Example:
            >>> client = GeminiClient()
            >>> image_data = client.generate_image(
            ...     prompt="Modern academic presentation title slide",
            ...     reference_images=[Path("ref1.png")],
            ...     aspect_ratio="16:9"
            ... )
        """
        logger.info(f"Generating image with prompt: {prompt[:100]}...")
        
        try:
            # Prepare reference images if provided
            reference_image_objects = []
            if reference_images:
                for ref in reference_images:
                    if isinstance(ref, Path):
                        ref_file = genai.upload_file(ref)
                    else:
                        ref_file = genai.upload_file(data=ref, mime_type="image/png")
                    reference_image_objects.append(ref_file)
                
                logger.debug(f"Uploaded {len(reference_image_objects)} reference images")
            
            # Generate image
            result = self._image_model.generate_images(
                prompt=prompt,
                reference_images=reference_image_objects if reference_image_objects else None,
                aspect_ratio=aspect_ratio,
                number_of_images=number_of_images,
                safety_filter_level="block_some",
            )
            
            # Get first generated image
            if result.images:
                image_data = result.images[0]._pil_image
                
                # Convert to bytes
                from io import BytesIO
                buffer = BytesIO()
                image_data.save(buffer, format='PNG')
                image_bytes = buffer.getvalue()
                
                logger.info(f"Generated image: {len(image_bytes)} bytes")
                
                return image_bytes
            else:
                raise Exception("No images generated")
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise
    
    def describe_image(self, image_path: Path) -> str:
        """
        Generate description of an image.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Image description
        
        Example:
            >>> client = GeminiClient()
            >>> description = client.describe_image(Path("figure1.png"))
        """
        logger.debug(f"Describing image: {image_path}")
        
        try:
            uploaded_image = genai.upload_file(image_path)
            
            response = self._text_model.generate_content(
                [
                    "Describe this image in detail, focusing on its content, "
                    "visual elements, and any text or diagrams present.",
                    uploaded_image
                ]
            )
            
            description = response.text
            logger.debug(f"Generated description: {len(description)} characters")
            
            return description
            
        except Exception as e:
            logger.error(f"Image description failed: {e}")
            raise
```

**Acceptance Criteria:**
- Gemini API properly configured
- Retry logic with exponential backoff
- Document upload and analysis works
- Image generation with reference images
- Comprehensive error handling

---

**Due to length constraints, I'll continue with the remaining tasks in a structured format. Would you like me to continue with:**

1. **Task 4.2**: Document Analyzer implementation
2. **Task 4.3**: Image Generator with reference image workflow
3. **Task 4.4**: Prompt templates
4. **Phase 4**: Presentation planning module
5. **Phase 5**: Main script and orchestration
6. **Phase 6**: Testing suite

Please confirm and I'll provide the next section with the same level of detail!