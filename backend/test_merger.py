import asyncio
import json
import logging
from app.core.report_merger import merge_reports

async def main():
    report1 = {"score": 85, "category_scores": {"security": 80}, "executive_summary": "Test 1", "risks": [{"severity": "high", "name": "Test risk 1"}], "why_not_80": ["Do this"]}
    report2 = {"source": "groq", "overall_score": 90, "executive_summary": "Test 2", "dimensions": {"security": {"score": 90, "conclusion": "good", "strengths": ["JWT"], "weaknesses": ["None"]}}, "top_risks": [], "roadmap": []}
    
    # We will call merge_reports
    res = await merge_reports(report1, report2)
    print("FINISHED")

asyncio.run(main())
