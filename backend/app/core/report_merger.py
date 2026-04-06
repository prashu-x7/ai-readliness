"""
Report Merger — sends Report1 + Report2 to Groq LLM to produce the Final Report.
Where both reports agree, confidence increases.
Where they disagree, both perspectives are noted.
"""
import httpx
import json
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MERGE_PROMPT = """You are an expert report merger. You have two independent analyses of the same codebase:

REPORT 1 (Local Static Engine — regex/hash pattern matching):
{report1}

REPORT 2 (AI LLM Analysis — deep semantic understanding):
{report2}

Merge them into ONE definitive final report following these rules:
1. Where both reports AGREE on a finding → mark as "high confidence"
2. Where they DISAGREE → include both perspectives with explanation
3. Take the LOWER score when scores differ (be conservative)
4. Combine all unique risks from both reports
5. Prioritize actionable recommendations
6. Generate an executive summary reflecting both analyses

Respond ONLY with valid JSON:
{{
  "final_score": int (0-100),
  "confidence": string ("high" if both agree, "medium" if partial, "low" if conflict),
  "executive_summary": string,
  "analysis_type": "dual_engine",
  "category_scores": {{
    "security": int,
    "data_protection": int,
    "api_quality": int,
    "infrastructure": int,
    "code_quality": int,
    "ai_ml_readiness": int,
    "performance": int,
    "compliance": int,
    "architecture": int
  }},
  "risks": [
    {{"text": string, "severity": string, "source": "local"|"llm"|"both", "confidence": string}}
  ],
  "strengths": [string],
  "improvements": [
    {{"action": string, "priority": "critical"|"high"|"medium"|"low", "impact": string}}
  ],
  "why_not_80": [string],
  "roadmap_to_80": [string]
}}"""


async def merge_reports(report1: dict, report2: dict) -> dict:
    """Merge Report1 (local) + Report2 (Groq) into a Final Report via LLM."""
    if report2.get("source") == "fallback" or not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
        logger.info("Report2 is fallback — using Report1 as final")
        return _promote_report1(report1)

    r1_summary = json.dumps(_compact(report1), indent=2)
    r2_summary = json.dumps(_compact(report2), indent=2)

    prompt = MERGE_PROMPT.replace("{report1}", r1_summary).replace("{report2}", r2_summary)

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
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
            final = json.loads(content)
            final["analysis_type"] = "dual_engine"
            final["report1_score"] = report1.get("score", 0)
            final["report2_score"] = report2.get("overall_score", 0)
            logger.info(f"Final merged report: score={final.get('final_score', '?')}")
            return final
    except Exception as e:
        logger.error(f"Merge failed: {e} — promoting Report1")
        return _promote_report1(report1)


def _compact(report: dict) -> dict:
    """Trim a report to essential fields for the merge prompt (token budget)."""
    if "score" in report:
        return {
            "score": report.get("score"),
            "category_scores": report.get("category_scores", {}),
            "risks": report.get("risks", [])[:15],
            "capabilities": report.get("capabilities", {}),
            "why_not_80": report.get("why_not_80", []),
        }
    return {
        "overall_score": report.get("overall_score"),
        "dimensions": {k: {"score": v.get("score"), "findings": v.get("findings", [])[:5]} for k, v in report.get("dimensions", {}).items()},
        "top_risks": report.get("top_risks", [])[:10],
        "roadmap": report.get("roadmap", [])[:10],
    }


def _promote_report1(report1: dict) -> dict:
    """When Groq is unavailable, wrap Report1 as the final report."""
    return {
        "final_score": report1.get("score", 0),
        "confidence": "medium",
        "executive_summary": report1.get("executive_summary", "Analysis complete using local engine only."),
        "analysis_type": "single_engine",
        "category_scores": report1.get("category_scores", {}),
        "risks": report1.get("risks", []),
        "strengths": [],
        "improvements": report1.get("improvement_diagnostics", []),
        "why_not_80": report1.get("why_not_80", []),
        "roadmap_to_80": report1.get("why_not_80", []),
        "report1_score": report1.get("score", 0),
        "report2_score": None,
    }
