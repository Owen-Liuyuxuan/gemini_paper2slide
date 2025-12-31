"""
FastAPI web application for paper-to-slide generation.

Provides REST API endpoints for:
- File upload and generation initiation
- Progress status polling
- Result retrieval
"""

import sys
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.progress import ProgressStage
from web.status_manager import JobStatusManager, JobStatus
from web.workflow_runner import run_generation_workflow

app = FastAPI(title="Paper to Slide Generator API")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize status manager (singleton)
status_manager = JobStatusManager()

# Directory paths
UPLOAD_DIR = Path(__file__).parent / "uploads"
OUTPUT_DIR = Path(__file__).parent / "outputs"
static_dir = Path(__file__).parent / "static"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.post("/api/generate-slides")
async def generate_slides(
    file: UploadFile = File(...),
    api_key: Optional[str] = Form(None),
    model_image: Optional[str] = Form(None),
    use_cache: Optional[str] = Form("true"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Start slide generation workflow.
    
    Uploads the PDF file and starts the generation process in the background.
    Returns immediately with a job_id for status polling.
    
    Args:
        file: Uploaded PDF file
        api_key: Google Gemini API key (optional, can also use environment variable)
        background_tasks: FastAPI background tasks
        use_cache: Whether to use cached intermediate results
    
    Returns:
        JSON response with job_id and status
    """
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Validate API key (required from frontend)
    if not api_key or not api_key.strip():
        raise HTTPException(
            status_code=400,
            detail="Google API key is required. Please provide your Google Gemini API key in the settings panel."
        )
    
    # Clean the API key
    api_key = api_key.strip()
    
    # Parse use_cache (comes as string from form)
    use_cache_bool = use_cache.lower() == "true" if use_cache else True
    
    # Validate model_image if provided
    valid_models = ["gemini-2.5-flash-image", "gemini-3-pro-image-preview"]
    if model_image and model_image not in valid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model_image. Must be one of: {', '.join(valid_models)}"
        )
    
    # Save uploaded file
    pdf_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    
    try:
        with open(pdf_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {str(e)}"
        )
    
    # Create output directory for this job
    output_dir = OUTPUT_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize job status BEFORE starting background task
    # This ensures the status is immediately available for polling
    status_manager.create_job(job_id)
    
    # Start background task
    background_tasks.add_task(
        run_generation_workflow,
        job_id=job_id,
        pdf_path=pdf_path,
        output_dir=output_dir,
        status_manager=status_manager,
        use_cache=use_cache_bool,
        api_key=api_key,
        model_image=model_image
    )
    
    return JSONResponse({
        "job_id": job_id,
        "status": "started",
        "message": "Generation started"
    })


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """
    Get current job status.
    
    Args:
        job_id: Job identifier returned from /api/generate-slides
    
    Returns:
        JSON response with current status, progress, and message
    """
    status = status_manager.get_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = {
        "job_id": job_id,
        "stage": status.stage.value,
        "progress": status.progress,
        "message": status.message,
        "details": status.details,
        "updated_at": status.updated_at.isoformat()
    }
    
    if status.error:
        response["error"] = status.error
    
    return JSONResponse(response)


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """
    Get generation results (PDF file).
    
    Args:
        job_id: Job identifier
    
    Returns:
        PDF file if generation is complete, or error if not ready
    """
    status = status_manager.get_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if status.stage != ProgressStage.COMPLETE:
        raise HTTPException(
            status_code=400,
            detail=f"Generation not complete. Current stage: {status.stage.value}"
        )
    
    # Look for PDF file in output directory
    output_dir = OUTPUT_DIR / job_id
    pdf_file = output_dir / "presentation.pdf"
    
    if not pdf_file.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF file not found in output directory"
        )
    
    return FileResponse(
        pdf_file,
        media_type="application/pdf",
        filename=f"presentation_{job_id}.pdf"
    )


@app.get("/api/results/{job_id}/slides")
async def get_slide_images(job_id: str):
    """
    Get list of generated slide images.
    
    Args:
        job_id: Job identifier
    
    Returns:
        JSON response with list of slide image URLs
    """
    status = status_manager.get_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if status.stage != ProgressStage.COMPLETE:
        raise HTTPException(
            status_code=400,
            detail=f"Generation not complete. Current stage: {status.stage.value}"
        )
    
    # List slide images in output directory
    output_dir = OUTPUT_DIR / job_id
    slide_files = sorted(output_dir.glob("slide_*.png"))
    
    slides = [
        {
            "filename": slide.name,
            "url": f"/api/files/{job_id}/{slide.name}"
        }
        for slide in slide_files
    ]
    
    return JSONResponse({
        "job_id": job_id,
        "slides": slides,
        "count": len(slides)
    })


@app.get("/api/files/{job_id}/{filename}")
async def get_file(job_id: str, filename: str):
    """
    Serve generated files (slides, PDF).
    
    Args:
        job_id: Job identifier
        filename: Name of the file to retrieve
    
    Returns:
        File response
    """
    output_dir = OUTPUT_DIR / job_id
    file_path = output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security: ensure file is within output directory
    try:
        file_path.resolve().relative_to(output_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Determine media type
    if filename.endswith('.png'):
        media_type = "image/png"
    elif filename.endswith('.pdf'):
        media_type = "application/pdf"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename
    )


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    favicon_path = static_dir / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/x-icon")
    raise HTTPException(status_code=404, detail="Favicon not found")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve frontend HTML"""
    index_file = static_dir / "index.html"
    if index_file.exists():
        with open(index_file, "r") as f:
            return f.read()
    return JSONResponse({
        "message": "Paper to Slide Generator API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/api/generate-slides",
            "status": "/api/status/{job_id}",
            "results": "/api/results/{job_id}",
            "slides": "/api/results/{job_id}/slides"
        }
    })


@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy"})

