"""FastAPI application for the LLM-TXT generator."""

import time
import uuid
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from ..worker.job_manager import JobManager
from .models import GenerationRequest, GenerationResponse, JobStatusResponse, HealthResponse
from .auth import verify_hmac_request
from ..worker.models import JobStatus
from .. import __version__
from .middleware import TimeoutMiddleware, RetryMiddleware, CircuitBreakerMiddleware

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize FastAPI app
app = FastAPI(
    title="LLM-TXT Generator",
    description="Generate LLM-friendly summaries from documentation URLs",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add reliability middleware (order matters - outermost first)
app.add_middleware(CircuitBreakerMiddleware, failure_threshold=10, timeout=30)
app.add_middleware(RetryMiddleware)
app.add_middleware(TimeoutMiddleware, timeout=60)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize job manager
job_manager = JobManager()


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info(f"Starting LLM-TXT API v{__version__}")
    logger.info("Warming up service...")
    # Pre-warm any connections or resources here if needed


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down LLM-TXT API")
    # Clean up any resources here if needed


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint with quick response."""
    return HealthResponse(
        status="healthy",
        version=__version__,
        timestamp=time.time()
    )


@app.post("/v1/generations", response_model=GenerationResponse, status_code=202)
async def create_generation(
    request_raw: Request,
    request: GenerationRequest,
    background_tasks: BackgroundTasks
) -> GenerationResponse:
    """Create a new generation job."""
    try:
        # Verify signed proxy call if required
        await verify_hmac_request(request_raw)
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create job
        job = await job_manager.create_job(
            job_id=job_id,
            url=str(request.url),
            max_pages=request.max_pages,
            max_depth=request.max_depth,
            full_version=request.full_version,
            respect_robots=request.respect_robots,
            language=request.language
        )
        
        # Start job in background
        background_tasks.add_task(job_manager.process_job, job_id)
        
        logger.info(f"Created generation job {job_id} for URL: {request.url}")
        
        return GenerationResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Generation job created successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to create generation job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create generation job")


@app.get("/v1/generations/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, response: Response, request: Request) -> JobStatusResponse:
    """Get the status of a generation job."""
    try:
        await verify_hmac_request(request)
        job = await job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        # Prevent intermediate caches from serving stale status
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return JobStatusResponse(
            job_id=job_id,
            status=job.status,
            progress=job.progress,
            message=job.message,
            created_at=job.created_at,
            completed_at=job.completed_at,
            current_phase=job.current_phase,
            current_page_url=job.current_page_url,
            pages_discovered=job.pages_discovered,
            pages_processed=job.pages_processed,
            processing_logs=job.processing_logs,
            pages_crawled=job.pages_crawled,
            total_size_kb=job.total_size_kb,
            llm_txt_url=job.llm_txt_url,
            llms_full_txt_url=job.llms_full_txt_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job status")


@app.get("/v1/generations/{job_id}/download/{file_type}")
async def download_result(job_id: str, file_type: str, request: Request):
    """Download generated files."""
    await verify_hmac_request(request)
    if file_type not in ["llm.txt", "llms-full.txt"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    try:
        content = await job_manager.get_result_file(job_id, file_type)
        
        if not content:
            raise HTTPException(status_code=404, detail="File not found or job not completed")
        # If raw=1, return plain text body for direct downloads
        raw = request.query_params.get("raw")
        headers = {
            "Content-Disposition": f"attachment; filename={file_type}",
            "Content-Type": "text/plain; charset=utf-8",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        if raw and raw.lower() in ("1", "true", "yes"):
            return PlainTextResponse(content, headers=headers)
        # Default: JSON wrapper used by programmatic clients
        return JSONResponse(content={"content": content}, headers=headers)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download result for {job_id}/{file_type}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download result")


@app.delete("/v1/generations/{job_id}")
async def cancel_job(job_id: str, request: Request) -> Dict[str, Any]:
    """Cancel a running job."""
    try:
        await verify_hmac_request(request)
        success = await job_manager.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or cannot be cancelled")
        
        logger.info(f"Cancelled job {job_id}")
        
        return {"message": "Job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel job")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Any, exc: Any) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Any, exc: Any) -> JSONResponse:
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
