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

MERGE_PROMPT = """You are an expert report merger and AI System Architect. You have two independent analyses of the same codebase:

REPORT 1 (Local Static Engine — regex/hash pattern matching):
{report1}

REPORT 2 (AI LLM Analysis — deep semantic understanding & raw directory map):
{report2}

Merge them into ONE definitive, highly detailed final report (Report 3) following these rules:
1. VERIFY Report 1 against Report 2. Use Report 2's AI capabilities to validate the static rules from Report 1.
2. Where both reports AGREE → mark as "high confidence" and elaborate on the finding.
3. Where they DISAGREE → highlight the discrepancy, explain why the static pattern might have triggered, and provide the AI's actual truth.
4. Provide an explicitly detailed "verification_notes" for each category, explaining how the AI evaluated the static findings.
5. Provide a raw "directory_structure_root" block based on Report 2's mapping.
6. Generate an extremely comprehensive reporting structure with robust details.

Respond ONLY with valid JSON exactly matching this schema:
{
  "assessment_id": "WILL_BE_INJECTED_LATER",
  "project_meta": { "language": "string", "frameworks": ["string"] },
  "final_score": int (0-100),
  "confidence_level": "High" | "Medium" | "Low",
  "executive_summary": "Extremely detailed multi-paragraph string integrating both analyses.",
  "architecture_assessment": {
    "directory_structure_root": "Raw directory tree or list of files",
    "directory_structure_map": "Deep analysis of the directory map",
    "connectivity_status": "How files interact",
    "ai_integration_readiness": "Readiness evaluation"
  },
  "layer_scores": {
    "security": int, "data_protection": int, "api_quality": int, "infrastructure": int,
    "code_quality": int, "ai_ml_readiness": int, "performance": int, "compliance": int, "architecture": int,
    "semantic_maintainability": int, "generative_ai_mapping": int, "data_processing_pipelines": int, "business_logic_modeling": int
  },
  "category_details": {
    "security": {
      "score": int, "report1_view": "string", "report2_view": "string",
      "merged_conclusion": "Detailed final verdict",
      "verification_notes": "How AI verified the static rules for this category",
      "discrepancies": ["string"],
      "strengths": ["string"], "weaknesses": ["string"]
    }
    // REPEAT for all 13 layers provided in Report 2!
  },
  "consolidated_risks": [
    {
      "severity": "critical" | "high" | "medium" | "low",
      "category": "string",
      "name": "string (Short title)",
      "issue": "string (Detailed description)",
      "found_by": "report1" | "report2" | "both",
      "recommendation": "string"
    }
  ],
  "action_roadmap": [
    { "step": int, "action": "string", "impact": "High" | "Medium" | "Low" }
  ]
}"""


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
    except httpx.HTTPStatusError as e:
        logger.error(f"Merge HTTP Error: {e.response.status_code} - {e.response.text} — promoting Report1")
        return _promote_report1(report1)
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
