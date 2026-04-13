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
Analyze the provided codebase summary.

First, reconstruct the mental map of the directory structure and how files connect.
Evaluate the architecture and explicitly answer the following questions:
- Is the application properly connected and modular?
- Is it ready for AI integration (e.g., vector databases, LLM context windows, RAG pipelines)?
- Does the code have distinct separation of concerns (MVC, Services, Data Layers)?
- Are the entity data models clearly defined and extensible?
- How uniquely testable is this codebase in its current state?

Then, evaluate the codebase across these 13 dimensions (9 static core + 4 semantic AI-specific):
1. security
2. data_protection
3. api_quality
4. infrastructure
5. code_quality
6. ai_ml_readiness
7. performance
8. compliance
9. architecture
10. semantic_maintainability       (Is the code logic understandable by an AI?)
11. generative_ai_mapping          (Which features can easily plug into GenAI?)
12. data_processing_pipelines      (Can the data layer pipe dynamically to vector stores?)
13. business_logic_modeling        (Are core concepts strictly enforced and clean?)

For each dimension, explicitly clarify:
- The top structural strengths and weaknesses.
- The exact impact on future AI feature expansion.
- Detailed connectivity or coupling issues affecting this dimension.
- Provide a clear, actionable conclusion.

Respond ONLY with valid JSON matching this schema exactly:
{
  "overall_score": int (0-100),
  "executive_summary": "string",
  "architecture_assessment": {
    "directory_structure_map": "Describe the directory tree and organization",
    "connectivity_status": "Describe how files interact (e.g. standard MVC, decoupled)",
    "ai_integration_readiness": "Specific evaluation of whether AI can be integrated here easily"
  },
  "dimensions": {
    "security": {
      "score": int,
      "conclusion": "string",
      "strengths": ["string"],
      "weaknesses": ["string"],
      "ai_readiness_impact": "string",
      "connectivity_issues": ["string"]
    }
    // REPEAT EXACTLY for all 13 dimensions
  },
  "top_risks": [{"text": "string", "severity": "critical"|"high"|"medium"|"low", "category": "string"}],
  "roadmap": [{"step": int, "action": "string", "impact": "High"}]
}"""


def _build_code_summary(file_entries: list[dict], classification: dict) -> str:
    """Build a compact summary of the codebase for the LLM prompt."""
    lines = []
    lines.append(f"Project Type: {classification.get('project_type', 'unknown')}")
    lines.append(f"Languages: {', '.join(classification.get('languages', []))}")
    lines.append(f"Frameworks: {', '.join(classification.get('frameworks', []))}")
    lines.append(f"Total Files: {len(file_entries)}")
    lines.append("")
    
    # Provide the raw directory structure map clearly
    lines.append("=== RAW DIRECTORY STRUCTURE MAP ===")
    for entry in file_entries:
        lines.append(entry.get("path", "unknown"))
    lines.append("===================================")
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
