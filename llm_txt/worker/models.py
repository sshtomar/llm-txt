"""Worker data models."""

import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class JobStatus(str, Enum):
    """Status of a generation job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Represents a generation job."""
    
    job_id: str
    url: str
    max_pages: int = 150
    max_depth: int = 5
    full_version: bool = False
    respect_robots: bool = True
    language: Optional[str] = "en"
    
    # Status tracking
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    message: str = ""
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    
    # Detailed progress tracking
    current_page_url: Optional[str] = None
    current_phase: str = "initializing"  # initializing, crawling, extracting, composing
    pages_discovered: int = 0
    pages_processed: int = 0
    processing_logs: List[str] = field(default_factory=list)  # Store processing logs
    
    # Results
    pages_crawled: Optional[int] = None
    total_size_kb: Optional[float] = None
    llm_txt_content: Optional[str] = None
    llms_full_txt_content: Optional[str] = None
    llm_txt_url: Optional[str] = None
    llms_full_txt_url: Optional[str] = None

    # Additional fields for S3 persistence
    llm_txt: Optional[str] = None  # Store the actual content
    llms_full_txt: Optional[str] = None  # Store the actual content

    # Error info
    error_message: Optional[str] = None
    error: Optional[str] = None  # Additional error field for S3 storage
    
    def set_status(self, status: JobStatus, message: str = "") -> None:
        """Update job status and message."""
        self.status = status
        self.message = message
        self.last_updated = time.time()
        
        if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            self.completed_at = time.time()
    
    def set_progress(self, progress: float, message: str = "") -> None:
        """Update job progress."""
        self.progress = max(0.0, min(1.0, progress))
        self.last_updated = time.time()
        if message:
            self.message = message
            # Add to processing logs with timestamp
            log_entry = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}"
            self.processing_logs.append(log_entry)
