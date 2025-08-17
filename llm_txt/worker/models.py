"""Worker data models."""

import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
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
    max_pages: int = 100
    max_depth: int = 3
    full_version: bool = False
    respect_robots: bool = True
    
    # Status tracking
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    message: str = ""
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    
    # Results
    pages_crawled: Optional[int] = None
    total_size_kb: Optional[float] = None
    llm_txt_content: Optional[str] = None
    llms_full_txt_content: Optional[str] = None
    llm_txt_url: Optional[str] = None
    llms_full_txt_url: Optional[str] = None
    
    # Error info
    error_message: Optional[str] = None
    
    def set_status(self, status: JobStatus, message: str = "") -> None:
        """Update job status and message."""
        self.status = status
        self.message = message
        
        if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            self.completed_at = time.time()
    
    def set_progress(self, progress: float, message: str = "") -> None:
        """Update job progress."""
        self.progress = max(0.0, min(1.0, progress))
        if message:
            self.message = message