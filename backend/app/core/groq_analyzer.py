"""
Groq LLM Analyzer — generates Report2 by sending code summary to Groq API.
Uses llama3-70b-8192 model for fast, high-quality AI readiness analysis.
"""
import httpx
import json
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are an expert code auditor specializing in AI readiness assessment.
Analyze the provided codebase summary and evaluate it across these 9 dimensions:
1. Security & Authentication
2. Data Protection & Privacy
3. API Quality & Design
4. Infrastructure & DevOps
5. Code Quality & Maintainability
6. AI/ML Integration Readiness
7. Performance & Scalability
8. Compliance & Observability
9. Architecture & Modularity

For each dimension, provide:
- score: 0-100
- findings: list of specific observations (what exists and what's missing)
- risks: list of risks with severity (critical/high/medium/low)
- recommendations: actionable improvement steps

Also provide:
- overall_score: 0-100
- executive_summary: 2-3 sentence overview
- top_risks: the 5 most critical risks
- roadmap: ordered list of improvements to reach 80+ score

Respond ONLY with valid JSON matching this schema:
{
  "overall_score": int,
  "executive_summary": string,
  "dimensions": {
    "security": {"score": int, "findings": [string], "risks": [{"text": string, "severity": string}], "recommendations": [string]},
    "data_protection": {...},
    "api_quality": {...},
    "infrastructure": {...},
    "code_quality": {...},
    "ai_ml_readiness": {...},
    "performance": {...},
    "compliance": {...},
    "architecture": {...}
  },
  "top_risks": [{"text": string, "severity": string}],
  "roadmap": [string]
}"""

def _build_code_summary(file_entries: list[dict], classification: dict) -> str:
    """Build a compact summary of the codebase for the LLM prompt."""
    lines = []
    lines.append(f"Project Type: {classification.get('project_type', 'unknown')}")
    lines.append(f"Languages: {', '.join(classification.get('languages', []))}")
    lines.append(f"Frameworks: {', '.join(classification.get('frameworks', []))}")
    lines.append(f"Total Files: {len(file_entries)}")
    lines.append("")

    for entry in file_entries[:60]:
        path = entry.get("path", "unknown")
        content = entry.get("content", "")
        if len(content) > 800:
            content = content[:400] + "\n... [truncated] ...\n" + content[-400:]
        lines.append(f"=== {path} ===")
        lines.append(content)
        lines.append("")

    return "\n".join(lines)


async def generate_report2(file_entries: list[dict], classification: dict) -> dict:
    """Call Groq API to generate Report2 (AI-powered analysis)."""
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
        logger.warning("GROQ_API_KEY not set — skipping LLM analysis")
        return _fallback_report2()

    code_summary = _build_code_summary(file_entries, classification)

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze this codebase for AI readiness:\n\n{code_summary}"},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            report2 = json.loads(content)
            report2["source"] = "groq_llm"
            report2["model"] = settings.GROQ_MODEL
            logger.info("Report2 generated successfully via Groq API")
            return report2
    except httpx.TimeoutException:
        logger.error("Groq API timeout — using fallback Report2")
        return _fallback_report2()
    except httpx.HTTPStatusError as e:
        logger.error(f"Groq API error {e.response.status_code}: {e.response.text}")
        return _fallback_report2()
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"Groq response parse error: {e}")
        return _fallback_report2()
    except Exception as e:
        logger.error(f"Groq unexpected error: {e}")
        return _fallback_report2()


def _fallback_report2() -> dict:
    """Return a minimal report when Groq API is unavailable."""
    return {
        "source": "fallback",
        "model": "none",
        "overall_score": None,
        "executive_summary": "LLM analysis unavailable — using local engine results only.",
        "dimensions": {},
        "top_risks": [],
        "roadmap": [],
    }
