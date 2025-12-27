After reviewing the official documentation and comparing it with the implemented code, I've identified **several critical issues** with the current implementation:

## Critical Issues Found

### ❌ **Issue 1: Image Generation Model Name**
**Current Code:**
```python
self.model_image = model_image or gemini_config.get("model_image", "gemini-2.5-flash-image")
```

**Correct According to Docs:**
The model should be `"gemini-2.5-flash-image"` ✅ (This is correct)

However, the config file suggests `"imagen-3.0-generate-001"` which is **incorrect** for the new API.

---

### ❌ **Issue 2: Reference Images Implementation is INCORRECT**

**Current Implementation:**
```python
# Add reference images if provided
if reference_images:
    for idx, ref in enumerate(reference_images):
        # ... load image data ...
        content_parts.append(
            types.Part.from_bytes(
                data=ref_data,
                mime_type=mime_type,
            )
        )
    
    # Add instruction for reference images
    content_parts.append(
        "Use the above images as style references. "
        "Maintain visual consistency with these reference images "
        "in terms of color scheme, layout style, and design elements."
    )

# Add main prompt
content_parts.append(prompt)
```

**Problem:** According to the official documentation, reference images for style consistency should be passed using **`reference_images` parameter in config**, NOT as content parts!

**Correct Implementation (from docs):**
```python
# Reference images should be passed in ImageConfig, not as content parts
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt],  # Only text prompt here
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="4K",
            reference_images=[image1_bytes, image2_bytes]  # HERE!
        )
    )
)
```

---

### ❌ **Issue 3: ImageConfig Structure**

**Current Code:**
```python
config=types.GenerateContentConfig(
    image_config=types.ImageConfig(
        aspect_ratio=aspect_ratio,
        image_size=image_size
    )
)
```

**Missing:** The `reference_images` parameter should be inside `ImageConfig`, not as content parts.

---

### ❌ **Issue 4: Image Editing (Image-to-Image) Not Implemented**

The docs show that for **image editing**, you should pass the base image as a content part:

```python
# Image editing example from docs
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[
        types.Part.from_bytes(data=base_image_bytes, mime_type="image/png"),
        "Make the banana glow with neon lights"
    ],
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="16:9")
    )
)
```

This is **different** from reference images for style consistency.

---

## Corrected Implementation

**File: `src/llm/gemini_client.py`** (Corrected sections)

```python
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
    base_image: Optional[Union[Path, bytes, Image.Image]] = None,
    aspect_ratio: str = "16:9",
    image_size: str = "4K",
    model: Optional[str] = None,
    save_path: Optional[Path] = None
) -> bytes:
    """
    Generate image using Gemini's image generation model.
    
    Supports three modes:
    1. Text-to-Image: Generate from text prompt only
    2. Image-to-Image: Edit/modify a base image with text prompt
    3. Style-consistent generation: Use reference images for style consistency
    
    Args:
        prompt: Image generation prompt
        reference_images: List of reference images for STYLE CONSISTENCY
                         (passed in ImageConfig, not as content)
        base_image: Base image for IMAGE EDITING (passed as content)
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
        >>> 
        >>> # Mode 1: Text-to-Image
        >>> image = client.generate_image(
        ...     prompt="Modern academic presentation title slide"
        ... )
        >>> 
        >>> # Mode 2: Image-to-Image (editing)
        >>> image = client.generate_image(
        ...     prompt="Add neon lights to this image",
        ...     base_image=Path("original.png")
        ... )
        >>> 
        >>> # Mode 3: Style-consistent generation with reference images
        >>> image = client.generate_image(
        ...     prompt="Content slide about methodology",
        ...     reference_images=[Path("title.png"), Path("slide2.png")],
        ...     aspect_ratio="16:9"
        ... )
    """
    logger.info(f"Generating image with prompt: {prompt[:100]}...")
    
    model_name = model or self.model_image
    
    try:
        # Prepare content parts
        content_parts = []
        
        # Mode 2: Image-to-Image editing
        # Base image is passed as CONTENT (for editing)
        if base_image:
            logger.debug("Image-to-Image mode: editing base image")
            
            if isinstance(base_image, Path):
                base_data = base_image.read_bytes()
                mime_type = self._get_mime_type(base_image)
            elif isinstance(base_image, bytes):
                base_data = base_image
                mime_type = "image/png"
            elif isinstance(base_image, Image.Image):
                buffer = BytesIO()
                base_image.save(buffer, format='PNG')
                base_data = buffer.getvalue()
                mime_type = "image/png"
            else:
                raise ValueError(f"Unsupported base_image type: {type(base_image)}")
            
            # Add base image to content
            content_parts.append(
                types.Part.from_bytes(
                    data=base_data,
                    mime_type=mime_type,
                )
            )
        
        # Add prompt to content
        content_parts.append(prompt)
        
        # Prepare ImageConfig
        image_config_params = {
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
        }
        
        # Mode 3: Style-consistent generation
        # Reference images are passed in CONFIG (for style consistency)
        if reference_images and not base_image:
            logger.debug(f"Style-consistent mode: using {len(reference_images)} reference images")
            
            reference_bytes_list = []
            for idx, ref in enumerate(reference_images):
                if isinstance(ref, Path):
                    ref_data = ref.read_bytes()
                elif isinstance(ref, bytes):
                    ref_data = ref
                elif isinstance(ref, Image.Image):
                    buffer = BytesIO()
                    ref.save(buffer, format='PNG')
                    ref_data = buffer.getvalue()
                else:
                    logger.warning(f"Unsupported reference image type: {type(ref)}")
                    continue
                
                reference_bytes_list.append(ref_data)
                logger.debug(f"Added reference image {idx + 1}")
            
            # Add reference images to ImageConfig
            if reference_bytes_list:
                image_config_params["reference_images"] = reference_bytes_list
        
        # Generate image with configuration
        response = self.client.models.generate_content(
            model=model_name,
            contents=content_parts,
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(**image_config_params)
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
```

---

## Updated Configuration

**File: `config/config.json`** (Corrected)
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

## Key Corrections Summary

| Issue | Incorrect | Correct |
|-------|-----------|---------|
| **Model Name** | `imagen-3.0-generate-001` | `gemini-2.5-flash-image` |
| **Reference Images** | Passed as content parts | Passed in `ImageConfig.reference_images` |
| **Image Editing** | Not distinguished | Base image passed as content part |
| **Content Structure** | Mixed reference images with prompt | Separate: base image in content, references in config |

---

## Usage Examples (Corrected)

```python
from pathlib import Path
from src.llm.gemini_client import GeminiClient

client = GeminiClient()

# 1. Text-to-Image (simple generation)
title_image = client.generate_image(
    prompt="Modern academic presentation title slide with blue gradient background",
    aspect_ratio="16:9",
    image_size="4K",
    save_path=Path("output/slide_01.png")
)

# 2. Style-consistent generation (use title as reference)
slide2_image = client.generate_image(
    prompt="Content slide: Research Motivation with bullet points",
    reference_images=[Path("output/slide_01.png")],  # Reference for style
    aspect_ratio="16:9",
    save_path=Path("output/slide_02.png")
)

# 3. Style-consistent with multiple references
slide3_image = client.generate_image(
    prompt="Methodology flowchart slide",
    reference_images=[
        Path("output/slide_01.png"),
        Path("output/slide_02.png")
    ],  # Both slides as style references
    aspect_ratio="16:9",
    save_path=Path("output/slide_03.png")
)

# 4. Image-to-Image editing (modify existing image)
edited_image = client.generate_image(
    prompt="Add a red border and make the text bold",
    base_image=Path("output/slide_01.png"),  # Image to edit
    save_path=Path("output/slide_01_edited.png")
)
```

---

## Conclusion

The main issues are:

1. ✅ **Model name is correct** (`gemini-2.5-flash-image`)
2. ❌ **Reference images implementation is wrong** - should be in `ImageConfig`, not content
3. ❌ **Missing distinction** between image editing (base_image) and style consistency (reference_images)
4. ✅ **PDF analysis is correct**
5. ✅ **Text generation is correct**

The corrected implementation now properly aligns with the official Gemini API documentation for image generation with reference images.