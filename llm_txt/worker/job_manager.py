"""Job manager for handling generation jobs."""

import asyncio
import logging
from typing import Dict, Optional
from .models import Job, JobStatus
from ..crawler import WebCrawler, CrawlConfig
from ..composer.composer import LLMTxtComposer

logger = logging.getLogger(__name__)


class JobManager:
    """Manages generation jobs and their lifecycle."""
    
    def __init__(self) -> None:
        self.jobs: Dict[str, Job] = {}
        self.composer = LLMTxtComposer()
    
    async def create_job(
        self,
        job_id: str,
        url: str,
        max_pages: int = 100,
        max_depth: int = 3,
        full_version: bool = False,
        respect_robots: bool = True
    ) -> Job:
        """Create a new generation job."""
        job = Job(
            job_id=job_id,
            url=url,
            max_pages=max_pages,
            max_depth=max_depth,
            full_version=full_version,
            respect_robots=respect_robots
        )
        
        self.jobs[job_id] = job
        logger.info(f"Created job {job_id} for URL: {url}")
        
        return job
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self.jobs.get(job_id)
    
    async def process_job(self, job_id: str) -> None:
        """Process a generation job."""
        job = self.jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        try:
            job.set_status(JobStatus.RUNNING, "Starting crawl...")
            job.set_progress(0.1, "Initializing crawler...")
            
            # Configure crawler
            crawl_config = CrawlConfig(
                max_pages=job.max_pages,
                max_depth=job.max_depth,
                respect_robots=job.respect_robots
            )
            
            crawler = WebCrawler(crawl_config)
            
            # Update progress
            job.set_progress(0.2, "Starting web crawl...")
            
            # Crawl the website
            crawl_result = crawler.crawl(job.url)
            
            job.pages_crawled = len(crawl_result.pages)
            job.set_progress(0.6, f"Crawled {job.pages_crawled} pages. Generating content...")
            
            if not crawl_result.pages:
                job.set_status(JobStatus.FAILED, "No pages could be crawled")
                return
            
            # Generate llm.txt content
            llm_txt_content = await self.composer.compose_llm_txt(crawl_result.pages)
            job.llm_txt_content = llm_txt_content
            
            # Calculate size
            job.total_size_kb = len(llm_txt_content.encode('utf-8')) / 1024
            
            # Generate full version if requested
            if job.full_version:
                job.set_progress(0.8, "Generating full version...")
                llms_full_content = await self.composer.compose_llms_full_txt(crawl_result.pages)
                job.llms_full_txt_content = llms_full_content
            
            # Set download URLs (in a real implementation, these would be actual URLs)
            job.llm_txt_url = f"/v1/generations/{job_id}/download/llm.txt"
            if job.full_version:
                job.llms_full_txt_url = f"/v1/generations/{job_id}/download/llms-full.txt"
            
            job.set_progress(1.0, "Generation completed successfully")
            job.set_status(JobStatus.COMPLETED, f"Generated {job.total_size_kb:.1f}KB of content")
            
            logger.info(f"Job {job_id} completed successfully. Crawled {job.pages_crawled} pages, generated {job.total_size_kb:.1f}KB")
            
        except Exception as e:
            error_msg = f"Job failed: {str(e)}"
            job.error_message = error_msg
            job.set_status(JobStatus.FAILED, error_msg)
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            job.set_status(JobStatus.CANCELLED, "Job cancelled by user")
            logger.info(f"Job {job_id} cancelled")
            return True
        
        return False
    
    async def get_result_file(self, job_id: str, file_type: str) -> Optional[str]:
        """Get the content of a result file."""
        job = self.jobs.get(job_id)
        if not job or job.status != JobStatus.COMPLETED:
            return None
        
        if file_type == "llm.txt":
            return job.llm_txt_content
        elif file_type == "llms-full.txt":
            return job.llms_full_txt_content
        
        return None