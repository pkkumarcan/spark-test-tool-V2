"""DuckDuckGo web research tool."""

from __future__ import annotations

import asyncio
import logging
import random
import re

import httpx

from packages.schemas.models import SandboxPolicy
from packages.tool_registry import tool

logger = logging.getLogger(__name__)


def _clean_html(html: str) -> str:
    html = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    text = re.sub(r'<.*?>', ' ', html)
    return re.sub(r'\s+', ' ', text).strip()[:8000]


async def _fetch_page(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            r = await client.get(url, headers=headers)
            if r.status_code == 200:
                return _clean_html(r.text)
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
    return ""


async def _search_ddg(query: str, max_results: int = 5) -> list[str]:
    """Search DuckDuckGo with multiple backend fallbacks."""
    from duckduckgo_search import DDGS

    backends = [None, "html", "lite"]
    for backend in backends:
        for attempt in range(2):
            try:
                if attempt > 0:
                    await asyncio.sleep(2.0 * attempt + random.random())
                with DDGS() as ddgs:
                    if backend:
                        results = list(ddgs.text(query, backend=backend, max_results=max_results))
                    else:
                        results = list(ddgs.text(query, max_results=max_results))
                    urls = [r["href"] for r in results if r.get("href")]
                    if urls:
                        return urls
            except Exception as e:
                err = str(e)
                if "202" in err or "RateLimit" in err.lower():
                    logger.warning(f"DDG rate-limited (backend={backend})")
                else:
                    logger.warning(f"DDG failed (backend={backend}): {e}")
    return []


@tool(
    "web_search",
    "Search the web for information on any topic. Returns search results with summaries.",
    sandbox_policy=SandboxPolicy(
        network_access=True,
        timeout_seconds=30,
        max_output_bytes=512 * 1024,
    ),
)
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web and return summarized results.

    Args:
        query: The search query.
        max_results: Maximum number of results to return (default 5).
    """
    urls = await _search_ddg(query, max_results=max_results)
    if not urls:
        return f"No search results found for: {query}"

    tasks = [_fetch_page(url) for url in urls[:max_results]]
    pages = await asyncio.gather(*tasks)

    results = []
    for url, text in zip(urls, pages):
        if text.strip():
            results.append(f"### {url}\n{text[:2000]}")

    if not results:
        return f"Found {len(urls)} URLs but could not extract content from any."

    return f"## Search results for: {query}\n\n" + "\n\n---\n\n".join(results)
