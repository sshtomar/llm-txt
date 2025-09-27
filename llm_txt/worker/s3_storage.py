"""S3-based storage for job persistence."""

import json
import logging
import os
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime, timedelta
import aioboto3
from botocore.exceptions import ClientError, NoCredentialsError

from .models import Job, JobStatus

logger = logging.getLogger(__name__)


class S3JobStorage:
    """S3-based storage adapter for job persistence."""

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region_name: str = "us-east-1",
        prefix: str = "jobs/"
    ):
        """Initialize S3 storage adapter.

        Args:
            bucket_name: S3 bucket name (or from env var S3_BUCKET_NAME)
            region_name: AWS region (default: us-east-1)
            prefix: S3 key prefix for jobs (default: jobs/)
        """
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME", "llm-txt-jobs")
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.prefix = prefix.rstrip("/") + "/"

        # Create aioboto3 session
        self.session = aioboto3.Session(
            region_name=self.region_name
        )

        logger.info(f"Initialized S3 storage: bucket={self.bucket_name}, region={self.region_name}")

    def _get_job_key(self, job_id: str, filename: str = "status.json") -> str:
        """Get S3 key for a job file."""
        return f"{self.prefix}{job_id}/{filename}"

    async def save_job(self, job: Job) -> bool:
        """Save job to S3.

        Args:
            job: Job instance to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize job to JSON
            job_data = {
                "job_id": job.job_id,
                "url": job.url,
                "status": job.status.value,
                "progress": job.progress,
                "message": job.message,
                "created_at": job.created_at,
                "completed_at": job.completed_at,
                "last_updated": getattr(job, "last_updated", None) or datetime.utcnow().timestamp(),
                "max_pages": job.max_pages,
                "max_depth": job.max_depth,
                "full_version": job.full_version,
                "respect_robots": job.respect_robots,
                "language": job.language,
                "current_phase": job.current_phase,
                "current_page_url": job.current_page_url,
                "pages_discovered": job.pages_discovered,
                "pages_processed": job.pages_processed,
                "pages_crawled": job.pages_crawled,
                "total_size_kb": job.total_size_kb,
                "processing_logs": job.processing_logs,
                "llm_txt_url": job.llm_txt_url,
                "llms_full_txt_url": job.llms_full_txt_url,
                "llm_txt": job.llm_txt,
                "llms_full_txt": job.llms_full_txt,
                "error": job.error,
                "last_updated": datetime.utcnow().timestamp()
            }

            job_json = json.dumps(job_data, indent=2)
            key = self._get_job_key(job.job_id)

            async with self.session.client("s3") as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=job_json.encode("utf-8"),
                    ContentType="application/json",
                    Metadata={
                        "status": job.status.value,
                        "url": job.url[:100],  # S3 metadata has size limits
                    }
                )

            logger.debug(f"Saved job {job.job_id} to S3: s3://{self.bucket_name}/{key}")
            return True

        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            return False
        except ClientError as e:
            logger.error(f"Failed to save job {job.job_id} to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving job {job.job_id}: {e}")
            return False

    async def load_job(self, job_id: str) -> Optional[Job]:
        """Load job from S3.

        Args:
            job_id: Job ID to load

        Returns:
            Job instance if found, None otherwise
        """
        try:
            key = self._get_job_key(job_id)

            async with self.session.client("s3") as s3:
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=key
                )

                body = await response["Body"].read()
                job_data = json.loads(body.decode("utf-8"))

            # Reconstruct Job instance
            job = Job(
                job_id=job_data["job_id"],
                url=job_data["url"],
                max_pages=job_data.get("max_pages", 100),
                max_depth=job_data.get("max_depth", 5),
                full_version=job_data.get("full_version", False),
                respect_robots=job_data.get("respect_robots", True),
                language=job_data.get("language", "en")
            )

            # Restore state
            job.status = JobStatus(job_data["status"])
            job.progress = job_data.get("progress", 0.0)
            job.message = job_data.get("message", "")
            job.created_at = job_data.get("created_at")
            job.completed_at = job_data.get("completed_at")
            # last_updated may not exist in older records; default to created_at
            try:
                job.last_updated = job_data.get("last_updated") or job_data.get("created_at")
            except Exception:
                pass
            job.current_phase = job_data.get("current_phase", "initializing")
            job.current_page_url = job_data.get("current_page_url")
            job.pages_discovered = job_data.get("pages_discovered", 0)
            job.pages_processed = job_data.get("pages_processed", 0)
            job.pages_crawled = job_data.get("pages_crawled", 0)
            job.total_size_kb = job_data.get("total_size_kb", 0.0)
            job.processing_logs = job_data.get("processing_logs", [])
            job.llm_txt = job_data.get("llm_txt")
            job.llms_full_txt = job_data.get("llms_full_txt")
            job.llm_txt_url = job_data.get("llm_txt_url")
            job.llms_full_txt_url = job_data.get("llms_full_txt_url")
            job.error = job_data.get("error")

            logger.debug(f"Loaded job {job_id} from S3")
            return job

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                logger.debug(f"Job {job_id} not found in S3")
            else:
                logger.error(f"Failed to load job {job_id} from S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading job {job_id}: {e}")
            return None

    async def save_result_file(self, job_id: str, filename: str, content: str) -> Optional[str]:
        """Save result file (llm.txt or llms-full.txt) to S3.

        Args:
            job_id: Job ID
            filename: File name (llm.txt or llms-full.txt)
            content: File content

        Returns:
            S3 URL if successful, None otherwise
        """
        try:
            key = self._get_job_key(job_id, filename)

            async with self.session.client("s3") as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=content.encode("utf-8"),
                    ContentType="text/plain; charset=utf-8",
                    Metadata={
                        "job_id": job_id,
                        "filename": filename
                    }
                )

            s3_url = f"s3://{self.bucket_name}/{key}"
            logger.debug(f"Saved result file {filename} for job {job_id}: {s3_url}")
            return s3_url

        except Exception as e:
            logger.error(f"Failed to save result file {filename} for job {job_id}: {e}")
            return None

    async def load_result_file(self, job_id: str, filename: str) -> Optional[str]:
        """Load result file from S3.

        Args:
            job_id: Job ID
            filename: File name (llm.txt or llms-full.txt)

        Returns:
            File content if found, None otherwise
        """
        try:
            key = self._get_job_key(job_id, filename)

            async with self.session.client("s3") as s3:
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=key
                )

                body = await response["Body"].read()
                content = body.decode("utf-8")

            logger.debug(f"Loaded result file {filename} for job {job_id}")
            return content

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                logger.debug(f"Result file {filename} not found for job {job_id}")
            else:
                logger.error(f"Failed to load result file {filename} for job {job_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading result file {filename} for job {job_id}: {e}")
            return None

    async def delete_job(self, job_id: str) -> bool:
        """Delete job and all associated files from S3.

        Args:
            job_id: Job ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            prefix = f"{self.prefix}{job_id}/"

            async with self.session.client("s3") as s3:
                # List all objects with this prefix
                paginator = s3.get_paginator("list_objects_v2")
                pages = paginator.paginate(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )

                # Delete all objects
                delete_objects = []
                async for page in pages:
                    if "Contents" in page:
                        for obj in page["Contents"]:
                            delete_objects.append({"Key": obj["Key"]})

                if delete_objects:
                    await s3.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={"Objects": delete_objects}
                    )

                logger.info(f"Deleted job {job_id} from S3 ({len(delete_objects)} objects)")
                return True

        except Exception as e:
            logger.error(f"Failed to delete job {job_id} from S3: {e}")
            return False

    async def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List jobs from S3.

        Args:
            status: Filter by status (optional)
            limit: Maximum number of jobs to return

        Returns:
            List of job metadata dictionaries
        """
        jobs = []

        try:
            async with self.session.client("s3") as s3:
                paginator = s3.get_paginator("list_objects_v2")
                pages = paginator.paginate(
                    Bucket=self.bucket_name,
                    Prefix=self.prefix,
                    Delimiter="/"
                )

                count = 0
                async for page in pages:
                    if "CommonPrefixes" in page:
                        for prefix_info in page["CommonPrefixes"]:
                            if count >= limit:
                                break

                            # Extract job_id from prefix
                            job_prefix = prefix_info["Prefix"]
                            job_id = job_prefix.replace(self.prefix, "").rstrip("/")

                            # Try to get job metadata
                            try:
                                key = self._get_job_key(job_id)
                                head_response = await s3.head_object(
                                    Bucket=self.bucket_name,
                                    Key=key
                                )

                                metadata = head_response.get("Metadata", {})
                                job_status = metadata.get("status", "unknown")

                                # Filter by status if specified
                                if status and job_status != status.value:
                                    continue

                                jobs.append({
                                    "job_id": job_id,
                                    "status": job_status,
                                    "url": metadata.get("url", ""),
                                    "last_modified": head_response.get("LastModified"),
                                    "size": head_response.get("ContentLength", 0)
                                })

                                count += 1

                            except ClientError:
                                continue

            logger.debug(f"Listed {len(jobs)} jobs from S3")
            return jobs

        except Exception as e:
            logger.error(f"Failed to list jobs from S3: {e}")
            return []

    async def cleanup_old_jobs(self, days: int = 7) -> int:
        """Clean up jobs older than specified days.

        Args:
            days: Delete jobs older than this many days

        Returns:
            Number of jobs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = 0

        try:
            jobs = await self.list_jobs()

            for job_meta in jobs:
                if job_meta.get("last_modified"):
                    last_modified = job_meta["last_modified"]
                    if hasattr(last_modified, "replace"):
                        # Remove timezone info for comparison
                        last_modified = last_modified.replace(tzinfo=None)

                    if last_modified < cutoff_date:
                        if await self.delete_job(job_meta["job_id"]):
                            deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} old jobs from S3")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old jobs: {e}")
            return deleted_count
