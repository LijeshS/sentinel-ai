import re
import time
import logging
import requests
from typing import List, Dict, Optional
from config import (
    BRIGHTDATA_API_KEY,
    BRIGHTDATA_USERNAME,
    BRIGHTDATA_PASSWORD,
    SERP_ENDPOINT,
    WEB_ACCESS_ENDPOINT,
    WEB_ACCESS_DATASET_ID,
    MCP_ENDPOINT,
    SEARCH_QUERIES,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
)

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _try_brightdata_serp(query: str) -> Optional[List[Dict]]:
    if not BRIGHTDATA_USERNAME or not BRIGHTDATA_PASSWORD:
        return None
    search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=5"
    payload = {"zone": "serp_api1", "url": search_url, "format": "raw"}
    try:
        resp = requests.post(
            SERP_ENDPOINT,
            auth=(BRIGHTDATA_USERNAME, BRIGHTDATA_PASSWORD),
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            return _parse_serp_html(resp.text)
        logger.warning(f"Bright Data SERP HTTP {resp.status_code}")
    except Exception as e:
        logger.warning(f"Bright Data SERP error: {e}")
    return None


def _direct_google_search(query: str) -> List[Dict]:
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=10"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            results = _parse_serp_html(resp.text)
            if results:
                return results
    except Exception as e:
        logger.warning(f"Google search failed: {e}")

    bing_url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
    try:
        resp = requests.get(bing_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return _parse_bing_html(resp.text)
    except Exception as e:
        logger.warning(f"Bing search failed: {e}")
    return []


def _parse_serp_html(html: str) -> List[Dict[str, str]]:
    results = []
    seen = set()
    patterns = [
        r'<a[^>]+href="(https?://(?!google\.|webcache\.|support\.google)[^"&]{20,})"[^>]*>.*?<h3[^>]*>(.*?)</h3>',
        r'href="(https?://(?!google\.|webcache\.)[^"&]{20,})"[^>]*>\s*<br[^>]*>(.*?)<',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, html, re.DOTALL)
        for url, raw_title in matches:
            title = re.sub(r"<[^>]+>", "", raw_title).strip()
            title = re.sub(r"\s+", " ", title)
            if title and url and url not in seen and len(title) > 5:
                seen.add(url)
                results.append({"title": title, "url": url})
            if len(results) >= 5:
                return results

    if not results:
        fallback = re.findall(
            r'href="(https?://(?!google\.com|webcache\.|bing\.com)[^"&]{20,})"[^>]*>([^<]{15,150})<',
            html
        )
        for url, title in fallback:
            title = title.strip()
            if title and url not in seen:
                seen.add(url)
                results.append({"title": title, "url": url})
            if len(results) >= 5:
                break
    return results[:5]


def _parse_bing_html(html: str) -> List[Dict[str, str]]:
    results = []
    seen = set()
    pattern = re.compile(
        r'<h2[^>]*>.*?<a[^>]+href="(https?://(?!bing\.com)[^"]+)"[^>]*>(.*?)</a>',
        re.DOTALL
    )
    for url, raw_title in pattern.findall(html):
        title = re.sub(r"<[^>]+>", "", raw_title).strip()
        if title and url not in seen:
            seen.add(url)
            results.append({"title": title, "url": url})
        if len(results) >= 5:
            break
    return results


def search_vendor_news(vendor_name: str) -> List[Dict[str, str]]:
    all_results = []
    seen_urls = set()

    for query_template in SEARCH_QUERIES:
        query = query_template.replace("{vendor}", vendor_name)
        logger.info(f"Searching: {query}")

        results = _try_brightdata_serp(query)
        if not results:
            results = _direct_google_search(query)

        for item in results:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_results.append(item)

        if len(all_results) >= 5:
            break

        time.sleep(1)

    logger.info(f"Found {len(all_results)} articles for {vendor_name}")
    return all_results[:10]


def extract_article(url: str) -> Optional[Dict[str, str]]:
    if BRIGHTDATA_USERNAME and BRIGHTDATA_PASSWORD:
        result = _try_brightdata_web_access(url)
        if result:
            return result
    return _fallback_extract(url)


def _try_brightdata_web_access(url: str) -> Optional[Dict]:
    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
        "Content-Type": "application/json",
    }
    endpoint = f"{WEB_ACCESS_ENDPOINT}?dataset_id={WEB_ACCESS_DATASET_ID}"
    try:
        resp = requests.post(
            endpoint,
            auth=(BRIGHTDATA_USERNAME, BRIGHTDATA_PASSWORD),
            json={"input": [{"url": url}]},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if isinstance(data, list) and data:
            item = data[0]
            content = item.get("content") or item.get("text") or item.get("description") or ""
            title = item.get("title") or item.get("name") or ""
            if content and len(content) > 50:
                return {"title": title, "content": content[:5000], "source_url": url}
    except Exception as e:
        logger.warning(f"Bright Data Web Access error: {e}")
    return None


def _fallback_extract(url: str) -> Optional[Dict[str, str]]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        html = resp.text
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = re.sub(r"\s+", " ", title_match.group(1).strip()) if title_match else ""
        for tag in ["script", "style", "nav", "header", "footer", "aside", "iframe"]:
            html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 100:
            return None
        return {"title": title, "content": text[:5000], "source_url": url}
    except Exception as e:
        logger.error(f"Fallback extract failed for {url}: {e}")
        return None


def query_mcp(prompt: str) -> Optional[str]:
    if not BRIGHTDATA_USERNAME or not BRIGHTDATA_PASSWORD:
        return None
    mcp_url = f"{MCP_ENDPOINT}?token={BRIGHTDATA_API_KEY}&groups=advanced_scraping"
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": "search_engine", "arguments": {"query": prompt}},
    }
    try:
        resp = requests.post(
            mcp_url,
            auth=(BRIGHTDATA_USERNAME, BRIGHTDATA_PASSWORD),
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            if "result" in data:
                result = data["result"]
                content = result.get("content", "") if isinstance(result, dict) else str(result)
                if isinstance(content, list):
                    return " ".join(c.get("text", "") for c in content if isinstance(c, dict))
                return str(content)
    except Exception as e:
        logger.error(f"MCP error: {e}")
    return None