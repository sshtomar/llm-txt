#!/usr/bin/env python3
"""Test S3 persistence functionality."""

import asyncio
import os
import json
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_txt.worker.s3_storage import S3JobStorage
from llm_txt.worker.models import Job, JobStatus


async def test_s3_persistence():
    """Test S3 persistence operations."""

    # Set environment variables
    os.environ["S3_BUCKET_NAME"] = "llm-txt-jobs"
    os.environ["AWS_REGION"] = "us-east-1"

    print("🚀 Testing S3 Persistence...")
    print(f"Bucket: {os.environ['S3_BUCKET_NAME']}")
    print(f"Region: {os.environ['AWS_REGION']}")
    print("-" * 50)

    # Initialize storage
    storage = S3JobStorage()

    # Create a test job
    test_job_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    job = Job(
        job_id=test_job_id,
        url="https://docs.python.org",
        max_pages=5,
        max_depth=2,
        full_version=True
    )

    print(f"✅ Created test job: {test_job_id}")

    # Test 1: Save job to S3
    print("\n📝 Test 1: Saving job to S3...")
    success = await storage.save_job(job)
    if success:
        print("   ✅ Job saved successfully")
    else:
        print("   ❌ Failed to save job")
        return

    # Test 2: Load job from S3
    print("\n📖 Test 2: Loading job from S3...")
    loaded_job = await storage.load_job(test_job_id)
    if loaded_job:
        print(f"   ✅ Job loaded successfully")
        print(f"   - Status: {loaded_job.status}")
        print(f"   - URL: {loaded_job.url}")
    else:
        print("   ❌ Failed to load job")
        return

    # Test 3: Update job status and save
    print("\n🔄 Test 3: Updating job status...")
    job.set_status(JobStatus.RUNNING, "Processing...")
    job.set_progress(0.5, "Halfway done")
    success = await storage.save_job(job)
    if success:
        print("   ✅ Job updated successfully")
    else:
        print("   ❌ Failed to update job")

    # Test 4: Save result files
    print("\n📄 Test 4: Saving result files...")
    test_content = "# Test LLM.txt\nThis is a test file for S3 persistence."

    llm_txt_url = await storage.save_result_file(test_job_id, "llm.txt", test_content)
    if llm_txt_url:
        print(f"   ✅ llm.txt saved: {llm_txt_url}")
    else:
        print("   ❌ Failed to save llm.txt")

    # Test 5: Load result file
    print("\n📥 Test 5: Loading result file...")
    loaded_content = await storage.load_result_file(test_job_id, "llm.txt")
    if loaded_content:
        print("   ✅ Result file loaded successfully")
        print(f"   - Content length: {len(loaded_content)} chars")
    else:
        print("   ❌ Failed to load result file")

    # Test 6: List jobs
    print("\n📋 Test 6: Listing jobs...")
    jobs = await storage.list_jobs(limit=5)
    print(f"   ✅ Found {len(jobs)} jobs in S3")
    for job_meta in jobs[:3]:  # Show first 3
        print(f"   - {job_meta['job_id']}: {job_meta['status']}")

    # Test 7: Clean up test job
    print("\n🗑️  Test 7: Cleaning up test job...")
    success = await storage.delete_job(test_job_id)
    if success:
        print("   ✅ Test job deleted successfully")
    else:
        print("   ❌ Failed to delete test job")

    print("\n" + "=" * 50)
    print("✅ All S3 persistence tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(test_s3_persistence())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()