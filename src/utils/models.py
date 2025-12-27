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


# Schemas for structured output from Gemini

class KeyPointSchema(BaseModel):
    """Schema for a key point in paper analysis (for structured output)."""
    title: str = Field(description="Short title for the key point")
    content: str = Field(description="Detailed content")
    importance: float = Field(ge=0.0, le=1.0, description="Importance score")
    section: str = Field(description="Source section")
    related_figure_pages: List[int] = Field(default_factory=list, description="Page numbers of related figures")


class FigureDescriptionSchema(BaseModel):
    """
    Schema for Gemini's description of a figure/table in the PDF.
    
    Gemini analyzes the PDF visually and describes figures without extraction.
    This avoids the PDF extraction problem where vector graphics are split into sub-elements.
    """
    page_number: int = Field(ge=1, description="Page number where figure appears")
    figure_number: Optional[str] = Field(None, description="Figure/table number or caption (e.g., 'Figure 1', 'Table 2')")
    figure_type: str = Field(description="Type of visual (figure, table, diagram, chart, plot, etc.)")
    visual_description: str = Field(
        description="Detailed description of what is shown visually (colors, layout, components, axes, etc.)"
    )
    content_description: str = Field(
        description="What data or concept the figure illustrates and key findings shown"
    )
    importance: float = Field(
        ge=0.0, le=1.0, 
        description="Importance for presentation (0-1)"
    )
    presentation_usage: str = Field(
        description="How this figure could be used in presentation slides"
    )


class PaperFiguresSchema(BaseModel):
    """
    Schema for comprehensive figure analysis from PDF using Gemini's vision.
    
    Contains all figures/tables identified by Gemini through direct PDF visual analysis,
    avoiding the need for fragile PDF image extraction.
    """
    total_figures: int = Field(ge=0, description="Total number of figures/tables identified")
    figures: List[FigureDescriptionSchema] = Field(
        default_factory=list,
        description="Detailed descriptions of each figure/table"
    )


class PaperAnalysisSchema(BaseModel):
    """Schema for paper analysis structured output."""
    summary: str = Field(description="Overall summary of the paper")
    research_question: str = Field(description="Main research question")
    methodology: str = Field(description="Research methodology description")
    key_contributions: List[str] = Field(min_items=1, description="Key contributions")
    key_points: List[KeyPointSchema] = Field(min_items=1, description="Detailed key points")
    recommended_slide_count: int = Field(ge=5, le=20, description="Recommended number of slides")
    visual_theme: str = Field(description="Suggested visual theme")


class SlideSpec(BaseModel):
    """Schema for a single slide specification (for structured output)."""
    index: int = Field(ge=0, description="Slide index")
    type: str = Field(description="Slide type (title, agenda, content, figure, conclusion)")
    title: str = Field(description="Slide title")
    key_points: List[str] = Field(description="Key points to cover (3-5 items)")
    visual_suggestions: str = Field(description="Visual element suggestions")
    related_figure_pages: List[int] = Field(default_factory=list, description="Page numbers of related figures")


class PresentationPlanSchema(BaseModel):
    """Schema for presentation plan structured output."""
    slide_count: int = Field(ge=5, le=20, description="Total number of slides")
    slides: List[SlideSpec] = Field(min_items=1, description="Slide specifications")
    style_description: str = Field(description="Overall presentation style description")
    presentation_flow: str = Field(description="Description of how the presentation flows")