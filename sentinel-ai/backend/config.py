import os
from dotenv import load_dotenv

load_dotenv()

BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sentinel.db")

SERP_ENDPOINT = "https://api.brightdata.com/request"
WEB_ACCESS_ENDPOINT = "https://api.brightdata.com/datasets/v3/scrape"
WEB_ACCESS_DATASET_ID = "gd_lvz8ah06191smkebj4"
MCP_ENDPOINT = "https://mcp.brightdata.com/mcp"

SCAN_INTERVAL_MINUTES = 5
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

DEFAULT_VENDORS = [
    "AWS",
    "Stripe",
    "Okta",
    "Cloudflare",
    "GitHub",
    "MongoDB",
    "Twilio",
]

SEARCH_QUERIES = [
    "{vendor} outage",
    "{vendor} breach",
    "{vendor} security incident",
    "{vendor} phishing",
    "{vendor} lawsuit",
    "{vendor} compliance issue",
]
