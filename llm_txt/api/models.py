"""API request and response models."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class JobStatus(str, Enum):
    """Status of a generation job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GenerationRequest(BaseModel):
    """Request model for generating llm.txt."""
    
    url: HttpUrl = Field(..., description="URL of the documentation site to crawl")
    max_pages: int = Field(150, ge=1, le=1000, description="Maximum pages to crawl")
    max_depth: int = Field(5, ge=1, le=10, description="Maximum crawl depth")
    full_version: bool = Field(False, description="Generate both llm.txt and llms-full.txt")
    respect_robots: bool = Field(True, description="Respect robots.txt directives")
    language: Optional[str] = Field("en", description="Preferred language (e.g., 'en'). Non-matching locale pages are skipped.")


class GenerationResponse(BaseModel):
    """Response model for generation request."""
    
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")


class JobStatusResponse(BaseModel):
    """Response model for job status check."""
    
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Progress percentage (0-1)")
    message: str = Field("", description="Status or error message")
    created_at: float = Field(..., description="Job creation timestamp")
    completed_at: Optional[float] = Field(None, description="Job completion timestamp")
    
    # Detailed progress info
    current_phase: str = Field("initializing", description="Current processing phase")
    current_page_url: Optional[str] = Field(None, description="URL of page currently being processed")
    pages_discovered: int = Field(0, description="Total pages discovered")
    pages_processed: int = Field(0, description="Pages processed so far")
    processing_logs: List[str] = Field(default_factory=list, description="Processing log entries")
    
    # Results (available when completed)
    pages_crawled: Optional[int] = Field(None, description="Number of pages successfully crawled")
    total_size_kb: Optional[float] = Field(None, description="Total size of generated content in KB")
    llm_txt_url: Optional[str] = Field(None, description="Download URL for llm.txt")
    llms_full_txt_url: Optional[str] = Field(None, description="Download URL for llms-full.txt")


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field("healthy", description="Service health status")
    version: str = Field(..., description="Service version")
    timestamp: float = Field(..., description="Response timestamp")
