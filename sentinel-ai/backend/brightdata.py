import re
import time
import logging
import requests
from typing import List, Dict, Optional
from config import (
    BRIGHTDATA_API_KEY,
    SERP_ENDPOINT,
    WEB_ACCESS_ENDPOINT,
    WEB_ACCESS_DATASET_ID,
    MCP_ENDPOINT,
    SEARCH_QUERIES,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
)

logger = logging.getLogger(__name__)


def _serp_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
        "Content-Type": "application/json",
    }


def _web_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
        "Content-Type": "application/json",
    }


def _retry_request(method: str, url: str, **kwargs) -> Optional[requests.Response]:
    for attempt in range(MAX_RETRIES):
        try:
            resp = getattr(requests, method)(url, timeout=REQUEST_TIMEOUT, **kwargs)
            if resp.status_code == 200:
                return resp
            logger.warning(f"Attempt {attempt + 1}: HTTP {resp.status_code} for {url}")
        except requests.exceptions.Timeout:
            logger.warning(f"Attempt {attempt + 1}: Timeout for {url}")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Attempt {attempt + 1}: Connection error for {url}: {e}")
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}: Unexpected error for {url}: {e}")
        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)
    return None


def _parse_serp_html(html: str) -> List[Dict[str, str]]:
    results = []

    # Extract search result links and titles from Google HTML
    # Pattern: <h3 class="...">title</h3> near href links
    link_pattern = re.compile(
        r'<a[^>]+href="(https?://(?!google\.|webcache\.)(?!www\.google\.)[^"&]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>',
        re.DOTALL,
    )
    matches = link_pattern.findall(html)

    for url, raw_title in matches:
        title = re.sub(r"<[^>]+>", "", raw_title).strip()
        title = re.sub(r"\s+", " ", title)
        if title and url and len(title) > 5:
            results.append({"title": title, "url": url})
        if len(results) >= 5:
            break

    # Fallback: extract any external links with text
    if not results:
        fallback_pattern = re.compile(
            r'href="(https?://(?!google\.com|webcache\.)[^"&]+)"[^>]*>([^<]{10,200})<',
            re.DOTALL,
        )
        for url, title in fallback_pattern.findall(html):
            title = title.strip()
            if title and len(results) < 5:
                results.append({"title": title, "url": url})

    return results[:5]


def search_vendor_news(vendor_name: str) -> List[Dict[str, str]]:
    all_results = []
    seen_urls = set()

    for query_template in SEARCH_QUERIES:
        query = query_template.replace("{vendor}", vendor_name)
        search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=5"

        payload = {
            "zone": "serp_api1",
            "url": search_url,
            "format": "raw",
        }

        logger.info(f"SERP search: {query}")
        resp = _retry_request("post", SERP_ENDPOINT, headers=_serp_headers(), json=payload)

        if resp is None:
            logger.warning(f"SERP failed for query: {query}")
            continue

        try:
            parsed = _parse_serp_html(resp.text)
            for item in parsed:
                if item["url"] not in seen_urls:
                    seen_urls.add(item["url"])
                    all_results.append(item)
        except Exception as e:
            logger.error(f"Error parsing SERP HTML for query '{query}': {e}")

        if len(all_results) >= 5:
            break

    return all_results[:10]


def extract_article(url: str) -> Optional[Dict[str, str]]:
    payload = {
        "dataset_id": WEB_ACCESS_DATASET_ID,
        "input": [{"url": url}],
    }

    logger.info(f"Web Access scrape: {url}")
    endpoint = f"{WEB_ACCESS_ENDPOINT}?dataset_id={WEB_ACCESS_DATASET_ID}"
    resp = _retry_request("post", endpoint, headers=_web_headers(), json={"input": [{"url": url}]})

    if resp is None:
        logger.warning(f"Web Access failed for URL: {url}")
        return _fallback_extract(url)

    try:
        data = resp.json()
        if isinstance(data, list) and data:
            item = data[0]
            title = item.get("title") or item.get("name") or ""
            content = (
                item.get("content")
                or item.get("text")
                or item.get("description")
                or item.get("body")
                or ""
            )
            if content and len(content) > 50:
                return {
                    "title": title,
                    "content": content[:5000],
                    "source_url": url,
                }
        elif isinstance(data, dict):
            content = (
                data.get("content")
                or data.get("text")
                or data.get("description")
                or ""
            )
            title = data.get("title") or data.get("name") or ""
            if content and len(content) > 50:
                return {
                    "title": title,
                    "content": content[:5000],
                    "source_url": url,
                }
    except Exception as e:
        logger.error(f"Error parsing Web Access response for {url}: {e}")

    return _fallback_extract(url)


def _fallback_extract(url: str) -> Optional[Dict[str, str]]:
    """Direct HTTP fallback when Bright Data is unavailable."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; SentinelAI/1.0; +https://sentinel.ai)",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None

        html = resp.text

        # Extract title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""
        title = re.sub(r"\s+", " ", title)

        # Strip scripts, styles, nav
        for tag in ["script", "style", "nav", "header", "footer", "aside"]:
            html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", " ", html, flags=re.DOTALL | re.IGNORECASE)

        # Extract text
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) < 100:
            return None

        return {
            "title": title,
            "content": text[:5000],
            "source_url": url,
        }
    except Exception as e:
        logger.error(f"Fallback extraction failed for {url}: {e}")
        return None


def query_mcp(prompt: str) -> Optional[str]:
    if not BRIGHTDATA_API_KEY:
        return None

    mcp_url = f"{MCP_ENDPOINT}?token={BRIGHTDATA_API_KEY}&groups=advanced_scraping"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search_engine",
            "arguments": {
                "query": prompt,
            },
        },
    }

    logger.info(f"MCP query: {prompt[:80]}")
    resp = _retry_request("post", mcp_url, headers=_web_headers(), json=payload)

    if resp is None:
        logger.warning("MCP request failed")
        return None

    try:
        data = resp.json()
        if "result" in data:
            result = data["result"]
            if isinstance(result, dict):
                content = result.get("content", "")
                if isinstance(content, list):
                    return " ".join(
                        c.get("text", "") for c in content if isinstance(c, dict)
                    )
                return str(content)
            return str(result)
        elif "error" in data:
            logger.error(f"MCP error: {data['error']}")
    except Exception as e:
        logger.error(f"MCP response parse error: {e}")

    return None
