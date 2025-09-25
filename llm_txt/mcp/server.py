"""MCP server that bridges LLM clients to the FastAPI backend.

This server exposes a single high-level tool `generate_llms_txt` that starts a
generation job against the FastAPI API, polls until completion (or timeout),
and returns the generated text content. It acts as a thin translation layer
without changing backend behavior.

Environment variables:
- LLM_TXT_API_BASE_URL: Base URL for the FastAPI backend (default: http://localhost:8000)
- LLM_TXT_API_TOKEN: Optional bearer token; adds `Authorization: Bearer <token>`
- LLM_TXT_API_TIMEOUT: Optional total wait seconds for job completion (default: 180)

Usage (as a binary):
- Installed via console script `llm-txt-mcp`, which runs this module's `main()`.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from dotenv import load_dotenv
import aiohttp
from mcp.server import Server
import mcp.types as types
from mcp.server.stdio import stdio_server


# Load .env if present
load_dotenv()


DEFAULT_BASE_URL = os.getenv("LLM_TXT_API_BASE_URL", "http://localhost:8000").rstrip("/")
DEFAULT_TIMEOUT = float(os.getenv("LLM_TXT_API_TIMEOUT", "180"))
API_TOKEN = os.getenv("LLM_TXT_API_TOKEN")


@dataclass
class ApiConfig:
    base_url: str = DEFAULT_BASE_URL
    bearer_token: Optional[str] = API_TOKEN
    total_wait_seconds: float = DEFAULT_TIMEOUT
    poll_interval_seconds: float = 1.5


def _auth_headers(token: Optional[str]) -> Dict[str, str]:
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# Note: use session.post/get directly with async-context manager


async def _start_generation(session: aiohttp.ClientSession, cfg: ApiConfig, *, url: str, max_pages: int, max_depth: int, full: bool, respect_robots: bool, language: Optional[str]) -> str:
    req = {
        "url": url,
        "max_pages": max_pages,
        "max_depth": max_depth,
        "full_version": full,
        "respect_robots": respect_robots,
        "language": language or "en",
    }
    async with session.post(f"{cfg.base_url}/v1/generations", json=req) as resp:
        if resp.status not in (200, 202):
            text = await resp.text()
            raise RuntimeError(f"Failed to create job ({resp.status}): {text}")
        data = await resp.json()
        job_id = data.get("job_id")
        if not job_id:
            raise RuntimeError("API did not return job_id")
        return job_id


async def _poll_status(session: aiohttp.ClientSession, cfg: ApiConfig, job_id: str) -> Dict[str, Any]:
    deadline = time.time() + cfg.total_wait_seconds
    last_status: Optional[str] = None
    while True:
        async with session.get(f"{cfg.base_url}/v1/generations/{job_id}") as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"Status check failed ({resp.status}): {text}")
            info = await resp.json()
        status = str(info.get("status", "")).lower()
        last_status = status or last_status
        if status in {"completed", "failed", "cancelled"}:
            return info
        if time.time() >= deadline:
            # Return the most recent info so callers can optionally keep polling.
            info["status"] = last_status or "running"
            info.setdefault("message", "Timed out waiting for completion")
            return info
        await asyncio.sleep(cfg.poll_interval_seconds)


async def _download_text(session: aiohttp.ClientSession, cfg: ApiConfig, job_id: str, file_type: str) -> Optional[str]:
    async with session.get(f"{cfg.base_url}/v1/generations/{job_id}/download/{file_type}") as resp:
        if resp.status == 404:
            return None
        if resp.status != 200:
            text = await resp.text()
            raise RuntimeError(f"Download failed ({resp.status}): {text}")
        # The API returns JSON payload but may set text/plain content-type.
        body = await resp.text()
        try:
            data = json.loads(body)
        except Exception:
            # Fallback to raw text
            return body
        return data.get("content")


server = Server("llm-txt-mcp")


async def _tool_generate_llms_txt(
    url: str,
    full: bool = False,
    max_pages: int = 100,
    max_depth: int = 5,
    max_kb: int = 500,  # Provided for parity; backend sizes via composer; returned value exposed from status
    respect_robots: bool = True,
    language: Optional[str] = "en",
    wait_seconds: Optional[float] = None,
) -> Dict[str, Any]:
    """Generate llm.txt (and optionally llms-full.txt) by calling the FastAPI backend.

    Parameters mirror the HTTP API. Returns a structured dict with job metadata
    and the resulting text content when available.
    """
    cfg = ApiConfig(
        base_url=os.getenv("LLM_TXT_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        bearer_token=os.getenv("LLM_TXT_API_TOKEN", API_TOKEN),
        total_wait_seconds=float(wait_seconds) if wait_seconds is not None else DEFAULT_TIMEOUT,
        poll_interval_seconds=1.5,
    )

    headers = {"Accept": "application/json", **_auth_headers(cfg.bearer_token)}
    timeout = aiohttp.ClientTimeout(total=cfg.total_wait_seconds + 30)

    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        job_id = await _start_generation(
            session,
            cfg,
            url=url,
            max_pages=max_pages,
            max_depth=max_depth,
            full=full,
            respect_robots=respect_robots,
            language=language,
        )

        status_info = await _poll_status(session, cfg, job_id)
        status = str(status_info.get("status", "")).lower()

        result: Dict[str, Any] = {
            "job_id": job_id,
            "status": status,
            "message": status_info.get("message", ""),
            "progress": status_info.get("progress"),
            "pages_crawled": status_info.get("pages_crawled"),
            "total_size_kb": status_info.get("total_size_kb"),
            "llm_txt": None,
            "llms_full_txt": None,
        }

        if status == "completed":
            # Download llm.txt
            result["llm_txt"] = await _download_text(session, cfg, job_id, "llm.txt")
            # Optionally download full version
            if full:
                result["llms_full_txt"] = await _download_text(session, cfg, job_id, "llms-full.txt")
        return result


async def _tool_get_generation_status(job_id: str) -> Dict[str, Any]:
    """Fetch job status without waiting. Useful for manual polling."""
    cfg = ApiConfig()
    headers = {"Accept": "application/json", **_auth_headers(cfg.bearer_token)}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{cfg.base_url}/v1/generations/{job_id}") as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"Status check failed ({resp.status}): {text}")
            return await resp.json()


async def _tool_cancel_generation(job_id: str) -> Dict[str, Any]:
    """Cancel a running job."""
    cfg = ApiConfig()
    headers = {"Accept": "application/json", **_auth_headers(cfg.bearer_token)}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.delete(f"{cfg.base_url}/v1/generations/{job_id}") as resp:
            text = await resp.text()
            if resp.status not in (200, 202):
                raise RuntimeError(f"Cancel failed ({resp.status}): {text}")
            try:
                return json.loads(text)
            except Exception:
                return {"message": text}


# Register tools using the mcp Server decorators available in this SDK version

@server.list_tools()
async def _list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_llms_txt",
            title="Generate llm.txt",
            description="Start a generation job and return llm.txt (and optionally llms-full.txt).",
            inputSchema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {"type": "string", "format": "uri"},
                    "full": {"type": "boolean", "default": False},
                    "max_pages": {"type": "integer", "minimum": 1, "default": 100},
                    "max_depth": {"type": "integer", "minimum": 1, "default": 5},
                    "max_kb": {"type": "integer", "minimum": 10, "default": 500},
                    "respect_robots": {"type": "boolean", "default": True},
                    "language": {"type": "string", "default": "en"},
                    "wait_seconds": {"type": "number", "minimum": 1, "default": DEFAULT_TIMEOUT},
                },
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "string"},
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                    "progress": {"type": ["number", "null"]},
                    "pages_crawled": {"type": ["integer", "null"]},
                    "total_size_kb": {"type": ["number", "null"]},
                    "llm_txt": {"type": ["string", "null"]},
                    "llms_full_txt": {"type": ["string", "null"]},
                },
                "required": ["job_id", "status"],
            },
        ),
        types.Tool(
            name="get_generation_status",
            title="Get job status",
            description="Fetch the current status of a generation job.",
            inputSchema={
                "type": "object",
                "required": ["job_id"],
                "properties": {"job_id": {"type": "string"}},
            },
            outputSchema={"type": "object"},
        ),
        types.Tool(
            name="cancel_generation",
            title="Cancel job",
            description="Cancel a running generation job.",
            inputSchema={
                "type": "object",
                "required": ["job_id"],
                "properties": {"job_id": {"type": "string"}},
            },
            outputSchema={"type": "object"},
        ),
    ]


@server.call_tool()
async def _call_tool(tool_name: str, arguments: Dict[str, Any]):
    if tool_name == "generate_llms_txt":
        return await _tool_generate_llms_txt(
            url=arguments["url"],
            full=arguments.get("full", False),
            max_pages=arguments.get("max_pages", 100),
            max_depth=arguments.get("max_depth", 5),
            max_kb=arguments.get("max_kb", 500),
            respect_robots=arguments.get("respect_robots", True),
            language=arguments.get("language", "en"),
            wait_seconds=arguments.get("wait_seconds"),
        )
    if tool_name == "get_generation_status":
        return await _tool_get_generation_status(job_id=arguments["job_id"])
    if tool_name == "cancel_generation":
        return await _tool_cancel_generation(job_id=arguments["job_id"])
    return {"error": f"Unknown tool: {tool_name}"}


async def _run() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    """Entry point for the `llm-txt-mcp` console script."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
