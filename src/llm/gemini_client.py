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
            
            # Check if response has text
            if not response.text:
                logger.warning("Empty response from API")
                return ""
            
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
        style_description: Optional[str] = None,
        base_image: Optional[Union[Path, Image.Image]] = None,
        aspect_ratio: str = "16:9",
        image_size: str = "4K",
        model: Optional[str] = None,
        save_path: Optional[Path] = None
    ) -> Image.Image:
        """
        Generate image using Gemini's image generation model.
        
        Supports two modes:
        1. Text-to-Image: Generate from text prompt only
        2. Image-to-Image: Edit/modify a base image with text prompt
        
        For visual consistency across slides, use enhanced prompts with style_description
        instead of reference images (which are not supported by the API).
        
        Args:
            prompt: Image generation prompt
            style_description: Optional style description for consistency (extracted from previous slides)
            base_image: Base image for IMAGE EDITING (passed as content)
            aspect_ratio: Image aspect ratio (16:9, 4:3, 1:1, 9:16, etc.)
            image_size: Image size (4K, 1080p, 720p)
            model: Model name (overrides default from config)
            save_path: Optional path to save generated image
        
        Returns:
            Generated PIL Image
        
        Raises:
            Exception: If generation fails
        
        Example:
            >>> client = GeminiClient()
            >>> 
            >>> # Mode 1: Text-to-Image
            >>> image = client.generate_image(
            ...     prompt="Modern academic presentation title slide with blue gradient"
            ... )
            >>> 
            >>> # Mode 1 with style consistency
            >>> style = "Blue gradient background, white text, clean sans-serif font, minimalist design"
            >>> image = client.generate_image(
            ...     prompt="Content slide about methodology",
            ...     style_description=style,
            ...     aspect_ratio="16:9"
            ... )
            >>> 
            >>> # Mode 2: Image-to-Image editing
            >>> image = client.generate_image(
            ...     prompt="Add emphasis to the title section",
            ...     base_image=Path("original.png")
            ... )
        """
        logger.info(f"Generating image with prompt: {prompt[:100]}...")
        
        # Use model from config, not hardcoded
        model_name = model or self.model_image
        
        try:
            # Enhance prompt with style description for consistency
            enhanced_prompt = prompt
            if style_description:
                logger.debug("Enhancing prompt with style description for consistency")
                # Load style consistency template from file
                style_template = self._load_prompt_template("style_consistency")
                style_text = style_template.format(style_description=style_description)
                enhanced_prompt = f"{prompt}\n\n{style_text}"
            
            # Generate image with or without base image
            if base_image is not None:
                # Mode 2: Image-to-Image (editing)
                if isinstance(base_image, Path):
                    base_image = Image.open(base_image)
                logger.debug("Image-to-Image mode: editing base image")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=[enhanced_prompt, base_image],
                )
            else:
                # Mode 1: Text-to-Image (generation)
                logger.debug("Text-to-Image mode: generating from prompt")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=enhanced_prompt,
                )
            
            # Extract image from response
            # The image is a special genai class, need to convert to PIL Image
            output_image = None
            for part in response.parts:
                if part.text is not None:
                    logger.debug(f"Response text: {part.text[:100]}...")
                elif part.inline_data is not None:
                    # Step 1: Get genai image object
                    output_image = part.as_image()
                    # Step 2: Convert genai image to PIL Image using image_bytes
                    output_image = Image.open(BytesIO(output_image.image_bytes))
                    break
            
            if output_image is None:
                raise Exception("No image generated in response")
            
            logger.info(f"Generated image: {output_image.size}")
            
            # Save if path provided
            if save_path:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                output_image.save(save_path)
                logger.info(f"Saved image to {save_path}")
            
            return output_image
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise
    
    def _load_prompt_template(self, template_name: str) -> str:
        """
        Load prompt template from file.
        
        Args:
            template_name: Name of template file (without .txt extension)
        
        Returns:
            Template content
        """
        template_file = Path("src/llm/prompts") / f"{template_name}.txt"
        try:
            return template_file.read_text()
        except FileNotFoundError:
            logger.warning(f"Template {template_file} not found, using default")
            # Return default for style consistency
            if template_name == "style_consistency":
                return """**Style Requirements for Visual Consistency:**
{style_description}

Ensure this slide maintains the same visual style, color scheme, and design language as described above."""
            return ""
    
    def extract_style_from_image(
        self,
        image_path: Optional[Path] = None,
        image_data: Optional[bytes] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Extract style description from an image for use in subsequent generations.
        
        This is used to maintain visual consistency across slides by describing
        the style of the first slide and using that description in prompts for
        subsequent slides.
        
        Args:
            image_path: Path to image file
            image_data: Raw image bytes (alternative to image_path)
            model: Model name (overrides default)
        
        Returns:
            Style description string
        
        Example:
            >>> client = GeminiClient()
            >>> style = client.extract_style_from_image(
            ...     image_path=Path("title_slide.png")
            ... )
            >>> print(style)
            "Blue gradient background from dark to light blue, white text in clean sans-serif font..."
        """
        if image_path is None and image_data is None:
            raise ValueError("Either image_path or image_data must be provided")
        
        logger.debug("Extracting style description from image")
        
        try:
            # Load image data if path provided
            if image_path and image_data is None:
                image_data = image_path.read_bytes()
                mime_type = self._get_mime_type(image_path)
            else:
                mime_type = "image/png"
            
            model_name = model or self.model_text
            
            style_extraction_prompt = """
Analyze this presentation slide image and provide a detailed style description that captures:

1. **Color Scheme**: Primary and secondary colors, background color/gradient
2. **Typography**: Font style (serif/sans-serif), text color, size hierarchy
3. **Layout Style**: Alignment, spacing, margins, visual balance
4. **Design Elements**: Any decorative elements, shapes, icons, borders
5. **Overall Aesthetic**: Modern/traditional, minimalist/detailed, professional/creative

Provide a concise but comprehensive description (100-150 words) that could be used to maintain visual consistency in subsequent slides.
Focus on objective visual characteristics rather than content.
"""
            
            # Generate style description
            response = self.client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(
                        data=image_data,
                        mime_type=mime_type,
                    ),
                    style_extraction_prompt
                ],
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Lower temperature for more consistent descriptions
                )
            )
            
            style_description = response.text
            logger.debug(f"Extracted style description: {style_description[:100]}...")
            
            return style_description
            
        except Exception as e:
            logger.error(f"Style extraction failed: {e}")
            # Return a default style if extraction fails
            return "Professional academic presentation style with clean layout and readable typography"
    
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
        pdf_path: Optional[Path] = None,
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> BaseModel:
        """
        Generate structured output using JSON schema validation.
        
        Uses Pydantic models to ensure type-safe responses.
        Optionally processes a PDF file as part of the input.
        
        Args:
            prompt: Input prompt
            response_schema: Pydantic model class for response structure
            pdf_path: Optional PDF file to analyze along with the prompt
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
            ...     response_schema=PaperSummary,
            ...     pdf_path=Path("paper.pdf")
            ... )
            >>> print(summary.title)
        """
        logger.info(f"Generating structured output: {response_schema.__name__}")
        
        model_name = model or self.model_text
        
        try:
            # Build content - can include PDF if provided
            if pdf_path:
                logger.debug(f"Including PDF in structured output: {pdf_path}")
                # Upload PDF file - accepts path string or file object
                file_ref = self.client.files.upload(file=str(pdf_path))
                content = [file_ref, prompt]
            else:
                content = prompt
            
            config = {
                "response_mime_type": "application/json",
                "response_json_schema": response_schema.model_json_schema(),
            }
            
            if tools:
                config["tools"] = tools
            
            response = self.client.models.generate_content(
                model=model_name,
                contents=content,
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