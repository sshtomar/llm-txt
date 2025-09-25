"""Local integration test for the MCP server against the FastAPI backend.

Spins up:
- A tiny local docs site on http://127.0.0.1:9999
- The FastAPI app on http://127.0.0.1:8000 (uvicorn, background thread)

Then calls the MCP tool function generate_llms_txt() and prints a summary.
"""

import asyncio
import os
import threading
import time
from typing import Optional

import aiohttp
from aiohttp import web


def _start_api_server() -> None:
    import uvicorn

    config = uvicorn.Config("llm_txt.api:app", host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    # Run with its own event loop
    asyncio.run(server.serve())


async def _start_docs_site() -> web.AppRunner:
    app = web.Application()

    async def docs(request: web.Request) -> web.Response:
        html = """
        <html><head><title>Test Docs</title></head>
        <body>
          <main>
            <h1>Getting Started</h1>
            <p>Install with pip: <code>pip install testpkg</code></p>
            <a href="/docs/page1">API Reference</a>
          </main>
        </body></html>
        """
        return web.Response(text=html, content_type="text/html")

    async def page1(request: web.Request) -> web.Response:
        html = """
        <html><head><title>API Reference</title></head>
        <body>
          <main>
            <h2>Client</h2>
            <pre><code>from testpkg import Client\nclient = Client(api_key="...")\nclient.run()</code></pre>
            <a href="/docs/page2">Examples</a>
          </main>
        </body></html>
        """
        return web.Response(text=html, content_type="text/html")

    async def page2(request: web.Request) -> web.Response:
        html = """
        <html><head><title>Examples</title></head>
        <body>
          <main>
            <h2>Examples</h2>
            <pre><code>print("hello world")</code></pre>
          </main>
        </body></html>
        """
        return web.Response(text=html, content_type="text/html")

    app.router.add_get("/docs", docs)
    app.router.add_get("/docs/page1", page1)
    app.router.add_get("/docs/page2", page2)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="127.0.0.1", port=9999)
    await site.start()
    return runner


async def _wait_for_health(url: str, timeout: float = 15.0) -> None:
    deadline = time.time() + timeout
    async with aiohttp.ClientSession() as session:
        while time.time() < deadline:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return
            except Exception:
                pass
            await asyncio.sleep(0.3)
    raise RuntimeError(f"Service at {url} did not become healthy in time")


async def main() -> None:
    # 1) Start the FastAPI app in a background thread
    api_thread = threading.Thread(target=_start_api_server, daemon=True)
    api_thread.start()

    # 2) Wait for API health
    await _wait_for_health("http://127.0.0.1:8000/health")

    # 3) Start the local docs site (lives in this event loop)
    runner = await _start_docs_site()

    # 4) Configure MCP to talk to our local API
    os.environ["LLM_TXT_API_BASE_URL"] = "http://127.0.0.1:8000"
    # Optional: os.environ["LLM_TXT_API_TOKEN"] = "..."
    os.environ["LLM_TXT_API_TIMEOUT"] = "60"

    # 5) Call the MCP tool directly (no stdio)
    from llm_txt.mcp.server import _tool_generate_llms_txt as generate_llms_txt

    result = await generate_llms_txt(
        url="http://127.0.0.1:9999/docs",
        full=False,
        max_pages=10,
        max_depth=2,
        respect_robots=False,
        language="en",
        wait_seconds=30,
    )

    status = result.get("status")
    llm_txt: Optional[str] = result.get("llm_txt")
    print({
        "status": status,
        "job_id": result.get("job_id"),
        "pages_crawled": result.get("pages_crawled"),
        "total_size_kb": result.get("total_size_kb"),
    })
    if llm_txt:
        print("\n--- llm.txt (first 400 chars) ---\n")
        print(llm_txt[:400])

    # 6) Cleanup docs runner
    await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
