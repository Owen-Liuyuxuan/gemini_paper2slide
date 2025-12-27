Based on the official Google Gemini API examples, I'll update the Gemini client implementation to use the correct `google.genai` SDK patterns.

## Updated Task 4.1: Implement Gemini Client (Revised)
**Priority: P0 | Estimated Time: 2 hours**

**File: `src/llm/gemini_client.py`**
```python
"""
Google Gemini API client with retry logic and error handling.

Provides unified interface for text generation, document analysis,
and image generation using the official google.genai SDK.
"""

import base64
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel
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
    Client for Google Gemini API using the official google.genai SDK.
    
    Handles text generation, document analysis, and image generation
    with automatic retry logic and error handling.
    
    Attributes:
        api_key: Google API key
        model_text: Text generation model name
        model_image: Image generation model name
        temperature: Generation temperature
        max_retries: Maximum retry attempts
        client: Gemini client instance
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
        
        Example:
            >>> client = GeminiClient()
            >>> # Or with custom config
            >>> client = GeminiClient(api_key="your-key", model_text="gemini-2.5-flash")
        """
        gemini_config = get_config("gemini", {})
        
        self.api_key = api_key or gemini_config.get("api_key")
        if not self.api_key:
            raise ValueError(
                "Google API key not provided. Set GOOGLE_API_KEY environment variable "
                "or provide api_key parameter."
            )
        
        self.model_text = model_text or gemini_config.get("model_text", "gemini-2.5-flash")
        self.model_image = model_image or gemini_config.get("model_image", "gemini-2.5-flash-image")
        self.temperature = temperature or gemini_config.get("temperature", 0.7)
        self.max_retries = max_retries or gemini_config.get("max_retries", 3)
        
        # Initialize client
        self.client = genai.Client(api_key=self.api_key)
        
        logger.info(
            f"GeminiClient initialized: text_model={self.model_text}, "
            f"image_model={self.model_image}, temperature={self.temperature}"
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
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Generate text using Gemini.
        
        Args:
            prompt: Input prompt
            temperature: Generation temperature (overrides default)
            max_tokens: Maximum tokens to generate
            model: Model name (overrides default)
        
        Returns:
            Generated text
        
        Raises:
            Exception: If generation fails after retries
        
        Example:
            >>> client = GeminiClient()
            >>> response = client.generate_text("Explain quantum computing")
            >>> print(response)
        """
        logger.debug(f"Generating text with prompt length: {len(prompt)}")
        
        model_name = model or self.model_text
        
        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature or self.temperature,
                    max_output_tokens=max_tokens or 8192,
                )
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
        prompt: str = "Analyze this document in detail.",
        model: Optional[str] = None,
        use_high_resolution: bool = False
    ) -> str:
        """
        Analyze PDF document using Gemini's multimodal capabilities.
        
        Uses the official google.genai SDK to process PDF documents directly.
        
        Args:
            pdf_path: Path to PDF file
            pdf_data: Raw PDF bytes (alternative to pdf_path)
            prompt: Analysis prompt
            model: Model name (overrides default)
            use_high_resolution: Use high resolution for better quality (v1alpha API)
        
        Returns:
            Analysis text
        
        Raises:
            ValueError: If neither pdf_path nor pdf_data provided
            Exception: If analysis fails
        
        Example:
            >>> client = GeminiClient()
            >>> # From file path
            >>> analysis = client.analyze_document(
            ...     pdf_path=Path("paper.pdf"),
            ...     prompt="Summarize the key contributions of this paper"
            ... )
            >>> # From bytes
            >>> with open("paper.pdf", "rb") as f:
            ...     pdf_bytes = f.read()
            >>> analysis = client.analyze_document(
            ...     pdf_data=pdf_bytes,
            ...     prompt="What is the main research question?"
            ... )
        """
        if pdf_path is None and pdf_data is None:
            raise ValueError("Either pdf_path or pdf_data must be provided")
        
        logger.info("Analyzing document with Gemini")
        
        try:
            # Load PDF data if path provided
            if pdf_path and pdf_data is None:
                logger.debug(f"Reading PDF from {pdf_path}")
                pdf_data = pdf_path.read_bytes()
            
            model_name = model or self.model_text
            
            # Create content parts
            parts = [
                types.Part.from_bytes(
                    data=pdf_data,
                    mime_type='application/pdf',
                )
            ]
            
            # Add high resolution parameter if requested (v1alpha API)
            if use_high_resolution:
                logger.debug("Using high resolution media processing")
                # Use v1alpha client for high resolution
                client_alpha = genai.Client(
                    api_key=self.api_key,
                    http_options={'api_version': 'v1alpha'}
                )
                
                response = client_alpha.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Content(
                            parts=[
                                types.Part(text=prompt),
                                types.Part(
                                    inline_data=types.Blob(
                                        mime_type="application/pdf",
                                        data=pdf_data,
                                    ),
                                    media_resolution={"level": "media_resolution_high"}
                                )
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=8192,
                    )
                )
            else:
                # Standard API
                parts.append(prompt)
                
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=parts,
                    config=types.GenerateContentConfig(
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
        reference_images: Optional[List[Union[Path, bytes, Image.Image]]] = None,
        aspect_ratio: str = "16:9",
        image_size: str = "4K",
        model: Optional[str] = None,
        save_path: Optional[Path] = None
    ) -> bytes:
        """
        Generate image using Gemini's image generation model.
        
        Uses the official google.genai SDK with support for reference images
        to maintain visual consistency across slides.
        
        Args:
            prompt: Image generation prompt
            reference_images: List of reference images (paths, bytes, or PIL Images)
            aspect_ratio: Image aspect ratio (16:9, 4:3, 1:1, 9:16, etc.)
            image_size: Image size (4K, 1080p, 720p)
            model: Model name (overrides default)
            save_path: Optional path to save generated image
        
        Returns:
            Generated image bytes (PNG format)
        
        Raises:
            Exception: If generation fails
        
        Example:
            >>> client = GeminiClient()
            >>> # Simple generation
            >>> image_data = client.generate_image(
            ...     prompt="Modern academic presentation title slide with blue theme"
            ... )
            >>> 
            >>> # With reference images for consistency
            >>> image_data = client.generate_image(
            ...     prompt="Content slide showing research methodology",
            ...     reference_images=[Path("title_slide.png"), Path("slide2.png")],
            ...     aspect_ratio="16:9",
            ...     image_size="4K"
            ... )
            >>> 
            >>> # Save directly
            >>> image_data = client.generate_image(
            ...     prompt="Conclusion slide",
            ...     save_path=Path("output/slide_10.png")
            ... )
        """
        logger.info(f"Generating image with prompt: {prompt[:100]}...")
        
        model_name = model or self.model_image
        
        try:
            # Prepare content parts
            content_parts = []
            
            # Add reference images if provided
            if reference_images:
                logger.debug(f"Processing {len(reference_images)} reference images")
                
                for idx, ref in enumerate(reference_images):
                    if isinstance(ref, Path):
                        # Load from file
                        ref_data = ref.read_bytes()
                        mime_type = self._get_mime_type(ref)
                    elif isinstance(ref, bytes):
                        # Already bytes
                        ref_data = ref
                        mime_type = "image/png"
                    elif isinstance(ref, Image.Image):
                        # Convert PIL Image to bytes
                        buffer = BytesIO()
                        ref.save(buffer, format='PNG')
                        ref_data = buffer.getvalue()
                        mime_type = "image/png"
                    else:
                        logger.warning(f"Unsupported reference image type: {type(ref)}")
                        continue
                    
                    # Add reference image part
                    content_parts.append(
                        types.Part.from_bytes(
                            data=ref_data,
                            mime_type=mime_type,
                        )
                    )
                    logger.debug(f"Added reference image {idx + 1}")
                
                # Add instruction for reference images
                content_parts.append(
                    "Use the above images as style references. "
                    "Maintain visual consistency with these reference images "
                    "in terms of color scheme, layout style, and design elements."
                )
            
            # Add main prompt
            content_parts.append(prompt)
            
            # Generate image with configuration
            response = self.client.models.generate_content(
                model=model_name,
                contents=content_parts,
                config=types.GenerateContentConfig(
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                        image_size=image_size
                    )
                )
            )
            
            # Extract image from response
            image_parts = [part for part in response.parts if part.inline_data]
            
            if not image_parts:
                raise Exception("No image generated in response")
            
            # Get the first image
            image = image_parts[0].as_image()
            
            # Convert to bytes
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            
            logger.info(f"Generated image: {len(image_bytes)} bytes")
            
            # Save if path provided
            if save_path:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(image_bytes)
                logger.info(f"Saved image to {save_path}")
            
            return image_bytes
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise
    
    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def describe_image(
        self,
        image_path: Optional[Path] = None,
        image_data: Optional[bytes] = None,
        prompt: str = "Describe this image in detail, focusing on its content, visual elements, and any text or diagrams present.",
        model: Optional[str] = None
    ) -> str:
        """
        Generate description of an image.
        
        Args:
            image_path: Path to image file
            image_data: Raw image bytes (alternative to image_path)
            prompt: Description prompt
            model: Model name (overrides default)
        
        Returns:
            Image description
        
        Raises:
            ValueError: If neither image_path nor image_data provided
        
        Example:
            >>> client = GeminiClient()
            >>> description = client.describe_image(
            ...     image_path=Path("figure1.png"),
            ...     prompt="What does this figure show?"
            ... )
        """
        if image_path is None and image_data is None:
            raise ValueError("Either image_path or image_data must be provided")
        
        logger.debug(f"Describing image: {image_path if image_path else 'from bytes'}")
        
        try:
            # Load image data if path provided
            if image_path and image_data is None:
                image_data = image_path.read_bytes()
                mime_type = self._get_mime_type(image_path)
            else:
                mime_type = "image/png"
            
            model_name = model or self.model_text
            
            # Create content with image and prompt
            response = self.client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(
                        data=image_data,
                        mime_type=mime_type,
                    ),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                )
            )
            
            description = response.text
            logger.debug(f"Generated description: {len(description)} characters")
            
            return description
            
        except Exception as e:
            logger.error(f"Image description failed: {e}")
            raise
    
    def generate_structured_output(
        self,
        prompt: str,
        response_schema: type[BaseModel],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> BaseModel:
        """
        Generate structured output using JSON schema validation.
        
        Uses Pydantic models to ensure type-safe responses.
        
        Args:
            prompt: Input prompt
            response_schema: Pydantic model class for response structure
            model: Model name (overrides default)
            tools: Optional tools to enable (e.g., google_search, url_context)
        
        Returns:
            Instance of response_schema with validated data
        
        Raises:
            Exception: If generation or validation fails
        
        Example:
            >>> from pydantic import BaseModel, Field
            >>> from typing import List
            >>> 
            >>> class PaperSummary(BaseModel):
            ...     title: str = Field(description="Paper title")
            ...     contributions: List[str] = Field(description="Key contributions")
            ...     methodology: str = Field(description="Research methodology")
            >>> 
            >>> client = GeminiClient()
            >>> summary = client.generate_structured_output(
            ...     prompt="Analyze this paper and extract key information",
            ...     response_schema=PaperSummary
            ... )
            >>> print(summary.title)
        """
        logger.info(f"Generating structured output: {response_schema.__name__}")
        
        model_name = model or self.model_text
        
        try:
            config = {
                "response_mime_type": "application/json",
                "response_json_schema": response_schema.model_json_schema(),
            }
            
            if tools:
                config["tools"] = tools
            
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            
            # Validate and parse response
            result = response_schema.model_validate_json(response.text)
            
            logger.info(f"Successfully generated structured output: {response_schema.__name__}")
            
            return result
            
        except Exception as e:
            logger.error(f"Structured output generation failed: {e}")
            raise
    
    def _get_mime_type(self, file_path: Path) -> str:
        """
        Get MIME type from file extension.
        
        Args:
            file_path: Path to file
        
        Returns:
            MIME type string
        """
        extension = file_path.suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
        }
        return mime_types.get(extension, 'application/octet-stream')
```

**Acceptance Criteria:**
- Uses official `google.genai` SDK correctly
- PDF document analysis with `types.Part.from_bytes()`
- Image generation with reference images for style consistency
- Support for high-resolution media processing (v1alpha)
- Structured output with Pydantic schema validation
- Comprehensive error handling and retry logic
- Proper MIME type detection

---

## Updated Configuration

**File: `config/config.json`** (Updated section)
```json
{
  "gemini": {
    "model_text": "gemini-2.5-flash",
    "model_image": "gemini-2.5-flash-image",
    "temperature": 0.7,
    "max_retries": 3,
    "retry_delay": 2,
    "timeout": 120
  },
  "image_generation": {
    "aspect_ratio": "16:9",
    "image_size": "4K",
    "use_reference_images": true,
    "max_reference_images": 2
  }
}
```

---

## Updated Requirements

**File: `requirements.txt`** (Updated)
```txt
# Core dependencies
google-genai>=0.3.0
PyMuPDF>=1.24.0
Pillow>=10.0.0

# HTTP client for document fetching
httpx>=0.25.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.0.0
tenacity>=8.2.0

# Logging and monitoring
loguru>=0.7.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# Development
black>=23.0.0
ruff>=0.1.0
mypy>=1.5.0
```

---

## Usage Examples

**File: `docs/examples/gemini_client_usage.py`**
```python
"""
Examples of using the GeminiClient for various tasks.
"""

from pathlib import Path
from pydantic import BaseModel, Field
from typing import List

from src.llm.gemini_client import GeminiClient


def example_text_generation():
    """Example: Basic text generation."""
    client = GeminiClient()
    
    response = client.generate_text(
        prompt="Explain the concept of attention mechanism in transformers."
    )
    print(response)


def example_pdf_analysis():
    """Example: Analyze a PDF document."""
    client = GeminiClient()
    
    # From file path
    analysis = client.analyze_document(
        pdf_path=Path("paper.pdf"),
        prompt="""
        Analyze this academic paper and provide:
        1. Main research question
        2. Key methodology
        3. Main contributions
        4. Important figures and their significance
        """
    )
    print(analysis)
    
    # With high resolution (for better quality)
    detailed_analysis = client.analyze_document(
        pdf_path=Path("paper.pdf"),
        prompt="Extract all mathematical equations and explain them.",
        use_high_resolution=True
    )
    print(detailed_analysis)


def example_image_generation():
    """Example: Generate images with reference images."""
    client = GeminiClient()
    
    # Generate title slide
    title_image = client.generate_image(
        prompt="""
        Create a modern, professional academic presentation title slide.
        Title: "Deep Learning for Autonomous Driving"
        Subtitle: "A Survey of Recent Advances"
        Style: Clean, minimalist, blue and white color scheme
        Include: Abstract geometric patterns suggesting AI and vehicles
        """,
        aspect_ratio="16:9",
        image_size="4K",
        save_path=Path("output/slide_01_title.png")
    )
    
    # Generate second slide using title as reference
    content_image = client.generate_image(
        prompt="""
        Create a content slide for "Research Motivation".
        Main points:
        - Increasing complexity of driving scenarios
        - Need for robust perception systems
        - Challenges in real-time processing
        
        Use bullet points with icons. Keep the design clean and readable.
        """,
        reference_images=[Path("output/slide_01_title.png")],
        aspect_ratio="16:9",
        image_size="4K",
        save_path=Path("output/slide_02_motivation.png")
    )
    
    # Generate subsequent slides with both references
    method_image = client.generate_image(
        prompt="""
        Create a content slide for "Proposed Methodology".
        Show a flowchart with three stages:
        1. Data Collection → 2. Model Training → 3. Deployment
        Use arrows to connect stages. Maintain consistent style.
        """,
        reference_images=[
            Path("output/slide_01_title.png"),
            Path("output/slide_02_motivation.png")
        ],
        aspect_ratio="16:9",
        save_path=Path("output/slide_03_methodology.png")
    )


def example_image_description():
    """Example: Describe extracted PDF images."""
    client = GeminiClient()
    
    description = client.describe_image(
        image_path=Path("extracted_images/figure_1.png"),
        prompt="""
        Describe this figure in detail:
        1. What type of visualization is it? (graph, diagram, photo, etc.)
        2. What are the main elements?
        3. What does it demonstrate or illustrate?
        4. Are there any labels, legends, or annotations?
        """
    )
    print(description)


def example_structured_output():
    """Example: Generate structured output with Pydantic."""
    
    class PaperAnalysis(BaseModel):
        title: str = Field(description="Paper title")
        research_question: str = Field(description="Main research question")
        methodology: str = Field(description="Research methodology")
        key_contributions: List[str] = Field(description="List of key contributions")
        important_figures: List[int] = Field(description="Page numbers of important figures")
        recommended_slides: int = Field(description="Recommended number of slides", ge=5, le=15)
    
    client = GeminiClient()
    
    # Analyze PDF and get structured output
    with open("paper.pdf", "rb") as f:
        pdf_data = f.read()
    
    # First get text analysis
    analysis_text = client.analyze_document(
        pdf_data=pdf_data,
        prompt="Analyze this paper comprehensively."
    )
    
    # Then extract structured information
    structured_analysis = client.generate_structured_output(
        prompt=f"""
        Based on this paper analysis, extract structured information:
        
        {analysis_text}
        
        Provide the information in the requested JSON format.
        """,
        response_schema=PaperAnalysis
    )
    
    print(f"Title: {structured_analysis.title}")
    print(f"Contributions: {structured_analysis.key_contributions}")
    print(f"Recommended slides: {structured_analysis.recommended_slides}")


def example_with_web_search():
    """Example: Use web search for current information."""
    
    class WeatherInfo(BaseModel):
        location: str = Field(description="Location name")
        temperature: str = Field(description="Current temperature")
        conditions: str = Field(description="Weather conditions")
        forecast: str = Field(description="Brief forecast")
    
    client = GeminiClient()
    
    weather = client.generate_structured_output(
        prompt="Get the current weather in Tokyo, Japan",
        response_schema=WeatherInfo,
        tools=[{"google_search": {}}]
    )
    
    print(f"Weather in {weather.location}:")
    print(f"Temperature: {weather.temperature}")
    print(f"Conditions: {weather.conditions}")


if __name__ == "__main__":
    # Run examples
    print("=== Text Generation ===")
    example_text_generation()
    
    print("\n=== PDF Analysis ===")
    example_pdf_analysis()
    
    print("\n=== Image Generation ===")
    example_image_generation()
    
    print("\n=== Image Description ===")
    example_image_description()
    
    print("\n=== Structured Output ===")
    example_structured_output()
```

---

## Key Updates Summary

### 1. **SDK Migration**
- Changed from `google.generativeai` to `google.genai`
- Uses `genai.Client()` for all operations
- Updated to official API patterns

### 2. **PDF Processing**
- Uses `types.Part.from_bytes()` for PDF input
- Supports both file paths and raw bytes
- Optional high-resolution processing with v1alpha API

### 3. **Image Generation**
- Uses `gemini-2.5-flash-image` model
- Reference images passed as content parts
- Supports `ImageConfig` with aspect ratio and size
- Returns PIL Image objects via `part.as_image()`

### 4. **Structured Output**
- Pydantic schema validation with `response_json_schema`
- Type-safe responses
- Support for tools (google_search, url_context)

### 5. **Error Handling**
- Tenacity retry decorators maintained
- Comprehensive logging
- Graceful fallbacks

This updated implementation aligns with the official Google Gemini API documentation and provides a robust foundation for the paper-to-slides system.