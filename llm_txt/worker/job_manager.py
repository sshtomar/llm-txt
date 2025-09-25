"""Job manager for handling generation jobs."""

import asyncio
import logging
import os
import time
from typing import Dict, Optional
from .models import Job, JobStatus
from .s3_storage import S3JobStorage
from ..crawler.async_crawler import AsyncWebCrawler
from ..crawler.models import CrawlConfig
from ..composer.composer import LLMTxtComposer

logger = logging.getLogger(__name__)


class JobManager:
    """Manages generation jobs and their lifecycle."""

    def __init__(self) -> None:
        # Keep in-memory cache for performance
        self.jobs: Dict[str, Job] = {}
        self.composer = LLMTxtComposer()

        # Initialize S3 storage if enabled
        self.use_s3 = os.getenv("USE_S3_STORAGE", "true").lower() == "true"
        self.s3_storage = S3JobStorage() if self.use_s3 else None

        if self.use_s3:
            logger.info("JobManager initialized with S3 persistence")
        else:
            logger.info("JobManager initialized with in-memory storage only")
    
    async def create_job(
        self,
        job_id: str,
        url: str,
        max_pages: int = 100,
        max_depth: int = 5,
        full_version: bool = False,
        respect_robots: bool = True,
        language: Optional[str] = "en"
    ) -> Job:
        """Create a new generation job."""
        job = Job(
            job_id=job_id,
            url=url,
            max_pages=max_pages,
            max_depth=max_depth,
            full_version=full_version,
            respect_robots=respect_robots,
            language=language
        )

        # Store in memory cache
        self.jobs[job_id] = job

        # Persist to S3 if enabled
        if self.s3_storage:
            await self.s3_storage.save_job(job)

        logger.info(f"Created job {job_id} for URL: {url}")

        return job
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        # Check memory cache first
        job = self.jobs.get(job_id)

        # If not in cache and S3 is enabled, try loading from S3
        if not job and self.s3_storage:
            job = await self.s3_storage.load_job(job_id)
            if job:
                # Add to cache for future access
                self.jobs[job_id] = job
                logger.debug(f"Loaded job {job_id} from S3")

        return job
    
    async def process_job(self, job_id: str) -> None:
        """Process a generation job."""
        job = await self.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        try:
            job.set_status(JobStatus.RUNNING, "Starting crawl...")
            job.current_phase = "initializing"
            job.set_progress(0.1, "Initializing crawler...")
            
            # Configure crawler with progress callback
            crawl_config = CrawlConfig(
                max_pages=job.max_pages,
                max_depth=job.max_depth,
                respect_robots=job.respect_robots,
                language=job.language
            )
            
            def update_crawl_progress(current_url: str, pages_done: int, pages_total: int):
                """Callback to update job progress during crawling."""
                job.current_page_url = current_url
                job.pages_discovered = pages_total
                job.pages_processed = pages_done
                progress = 0.2 + (0.4 * (pages_done / max(pages_total, 1)))
                job.set_progress(progress, f"Crawling: {current_url[:50]}...")
                # Save progress to S3 periodically
                if self.s3_storage and pages_done % 10 == 0:
                    asyncio.create_task(self.s3_storage.save_job(job))
            
            crawler = AsyncWebCrawler(crawl_config, progress_callback=update_crawl_progress)
            
            # Update progress
            job.current_phase = "crawling"
            job.set_progress(0.2, "Starting web crawl...")

            # Save initial state to S3
            if self.s3_storage:
                await self.s3_storage.save_job(job)
            
            # Crawl the website (now async)
            crawl_result = await crawler.crawl(job.url)
            
            job.pages_crawled = len(crawl_result.pages)
            job.current_phase = "extracting"
            job.set_progress(0.6, f"Crawled {job.pages_crawled} pages. Extracting content...")
            
            # Add detailed stats to logs
            if crawl_result.pages:
                total_chars = sum(len(p.content) for p in crawl_result.pages)
                if job.pages_discovered > 0:
                    job.processing_logs.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Found {job.pages_discovered} URLs to crawl")
                job.processing_logs.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Total content size: {total_chars} characters")
            
            # Log if there were blocked URLs
            if crawl_result.blocked_urls:
                job.processing_logs.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {len(crawl_result.blocked_urls)} URLs blocked by robots.txt")
            
            if not crawl_result.pages:
                job.set_status(JobStatus.FAILED, "No pages could be crawled")
                if self.s3_storage:
                    await self.s3_storage.save_job(job)
                return
            
            # Generate llm.txt content
            job.current_phase = "composing"
            job.current_page_url = None
            job.set_progress(0.7, "Composing llm.txt with AI...")
            
            llm_txt_content = await self.composer.compose_llm_txt(crawl_result.pages)
            job.llm_txt_content = llm_txt_content
            job.llm_txt = llm_txt_content  # Store in the job model field

            # Save llm.txt to S3
            if self.s3_storage:
                s3_url = await self.s3_storage.save_result_file(job_id, "llm.txt", llm_txt_content)
                if s3_url:
                    job.llm_txt_url = s3_url
            
            # Calculate size
            job.total_size_kb = len(llm_txt_content.encode('utf-8')) / 1024
            
            # Log AI summarization results
            original_size = sum(len(p.content) for p in crawl_result.pages)
            final_size = len(llm_txt_content)
            reduction_pct = ((original_size - final_size) / original_size * 100) if original_size > 0 else 0
            job.processing_logs.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - AI summarization completed. Original: {original_size} chars, Summary: {final_size} chars")
            job.processing_logs.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Size reduction: {reduction_pct:.1f}%")
            
            # Run quality validation
            is_valid, issues = self.composer._validate_output_quality(llm_txt_content)
            if is_valid:
                job.processing_logs.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Output quality validation: PASSED")
            else:
                job.processing_logs.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Output quality validation: FAILED - {', '.join(issues)}")
            
            # Generate full version if requested
            if job.full_version:
                job.set_progress(0.8, "Generating full version...")
                llms_full_content = await self.composer.compose_llms_full_txt(crawl_result.pages)
                job.llms_full_txt_content = llms_full_content
                job.llms_full_txt = llms_full_content  # Store in the job model field

                # Save llms-full.txt to S3
                if self.s3_storage:
                    s3_url = await self.s3_storage.save_result_file(job_id, "llms-full.txt", llms_full_content)
                    if s3_url:
                        job.llms_full_txt_url = s3_url
            
            # Set download URLs (in a real implementation, these would be actual URLs)
            job.llm_txt_url = f"/v1/generations/{job_id}/download/llm.txt"
            if job.full_version:
                job.llms_full_txt_url = f"/v1/generations/{job_id}/download/llms-full.txt"
            
            job.set_progress(1.0, "Generation completed successfully")
            job.set_status(JobStatus.COMPLETED, f"Generated {job.total_size_kb:.1f}KB of content")

            # Save final state to S3
            if self.s3_storage:
                await self.s3_storage.save_job(job)

            logger.info(f"Job {job_id} completed successfully. Crawled {job.pages_crawled} pages, generated {job.total_size_kb:.1f}KB")
            
        except Exception as e:
            error_msg = f"Job failed: {str(e)}"
            job.error_message = error_msg
            job.error = str(e)  # Store in the job model field
            job.set_status(JobStatus.FAILED, error_msg)

            # Save error state to S3
            if self.s3_storage:
                await self.s3_storage.save_job(job)

            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        job = await self.get_job(job_id)
        if not job:
            return False

        if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            job.set_status(JobStatus.CANCELLED, "Job cancelled by user")

            # Save cancellation to S3
            if self.s3_storage:
                await self.s3_storage.save_job(job)

            logger.info(f"Job {job_id} cancelled")
            return True

        return False
    
    async def get_result_file(self, job_id: str, file_type: str) -> Optional[str]:
        """Get the content of a result file."""
        job = await self.get_job(job_id)
        if not job or job.status != JobStatus.COMPLETED:
            return None

        # Try memory cache first
        if file_type == "llm.txt" and job.llm_txt_content:
            return job.llm_txt_content
        elif file_type == "llms-full.txt" and job.llms_full_txt_content:
            return job.llms_full_txt_content

        # Try loading from S3 if not in memory
        if self.s3_storage:
            content = await self.s3_storage.load_result_file(job_id, file_type)
            if content:
                # Cache for future use
                if file_type == "llm.txt":
                    job.llm_txt_content = content
                elif file_type == "llms-full.txt":
                    job.llms_full_txt_content = content
                return content

        return None
