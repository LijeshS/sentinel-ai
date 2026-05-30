import json
import logging
from typing import Optional, Dict
from openai import OpenAI
from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are an enterprise security risk analyst specializing in third-party vendor risk management.

Your task is to analyze news articles and content about vendors and assess security/operational risks.

Return ONLY a valid JSON object — no markdown, no explanation, no preamble.

If the article is genuinely irrelevant to vendor risk (unrelated news, product announcements, tutorials, etc.), return exactly: null

Otherwise return this exact JSON structure:
{
  "vendor": "<vendor name>",
  "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "incident_type": "<concise type e.g. Data Breach, Service Outage, Compliance Violation, Phishing Campaign, Ransomware, Supply Chain Attack, DDoS, Insider Threat, API Vulnerability, Third-Party Risk>",
  "summary": "<2-3 sentence factual summary of the incident>",
  "business_impact": "<1-2 sentences describing potential business impact for enterprise customers>",
  "recommended_action": "<1-2 sentences of concrete recommended action for security teams>"
}

Risk level guidance:
- CRITICAL: Active breach with data exfiltration, ransomware, complete service failure affecting production
- HIGH: Security vulnerability being exploited, significant outage, regulatory enforcement action
- MEDIUM: Unconfirmed breach reports, partial outage, compliance warnings, phishing campaigns
- LOW: Minor performance issues, precautionary advisories, historical incidents now resolved

Consider: scope of impact, data sensitivity, duration, affected enterprise customers, regulatory implications."""


def analyze_article(
    vendor_name: str,
    article_title: str,
    article_content: str,
    source_url: str,
) -> Optional[Dict]:
    if not OPENAI_API_KEY:
        logger.warning("No OpenAI API key configured, using mock analysis")
        return _mock_analysis(vendor_name, article_title, source_url)

    content_preview = article_content[:3000] if article_content else ""
    user_message = f"""Vendor: {vendor_name}

Article Title: {article_title}

Article Content:
{content_preview}

Source URL: {source_url}

Analyze this content for security/operational risks related to {vendor_name}. Return JSON or null."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=600,
        )

        raw = response.choices[0].message.content.strip()
        logger.info(f"AI response for {vendor_name}: {raw[:100]}")

        if raw.lower() == "null" or raw == "":
            return None

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        result = json.loads(raw)

        # Validate required fields
        required = ["vendor", "risk_level", "incident_type", "summary", "business_impact", "recommended_action"]
        if not all(k in result for k in required):
            logger.warning(f"AI response missing required fields: {result}")
            return None

        valid_levels = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        if result["risk_level"] not in valid_levels:
            result["risk_level"] = "MEDIUM"

        return result

    except json.JSONDecodeError as e:
        logger.error(f"AI response JSON parse error for {vendor_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"OpenAI API error for {vendor_name}: {e}")
        return None


def _mock_analysis(vendor_name: str, article_title: str, source_url: str) -> Optional[Dict]:
    """Mock analysis when OpenAI key is not configured — for demo purposes."""
    import random

    title_lower = article_title.lower()

    # Determine relevance
    risk_keywords = ["breach", "outage", "hack", "security", "incident", "vulnerability",
                     "phishing", "ransomware", "leak", "attack", "failure", "down", "lawsuit"]
    if not any(kw in title_lower for kw in risk_keywords):
        return None

    levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    weights = [0.3, 0.4, 0.2, 0.1]
    risk_level = random.choices(levels, weights=weights)[0]

    incident_types = {
        "breach": "Data Breach",
        "outage": "Service Outage",
        "hack": "Security Compromise",
        "phishing": "Phishing Campaign",
        "ransomware": "Ransomware Attack",
        "vulnerability": "API Vulnerability",
        "leak": "Data Leak",
        "down": "Service Outage",
        "lawsuit": "Regulatory Action",
    }

    incident_type = "Security Incident"
    for kw, itype in incident_types.items():
        if kw in title_lower:
            incident_type = itype
            break

    return {
        "vendor": vendor_name,
        "risk_level": risk_level,
        "incident_type": incident_type,
        "summary": f"Reports indicate a {incident_type.lower()} affecting {vendor_name}. Security teams are investigating the scope and impact. Further details are expected as the situation develops.",
        "business_impact": f"Enterprise customers relying on {vendor_name} services may experience disruptions or elevated security risk. Immediate review of service dependencies is recommended.",
        "recommended_action": f"Monitor {vendor_name} status page and security advisories. Review your organization's contingency plans and consider activating incident response procedures if critical services are affected.",
    }
