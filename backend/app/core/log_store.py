"""
log_store.py — Persist assessment logs and reports to the /logs/ folder.
Creates: logs/{assessment_id}/report.json, summary.txt, metadata.json
"""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("app_reader.log_store")

LOGS_ROOT = Path(__file__).parent.parent.parent / "logs"

def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def save_assessment_log(
    assessment_id: str,
    user_id: str,
    source_value: str,
    source_type: str,
    score: int,
    status: str,
    report: dict[str, Any],
) -> Path:
    """
    Persist full report JSON + human-readable summary to /logs/{assessment_id}/
    Returns the log directory path.
    """
    log_dir = LOGS_ROOT / assessment_id
    _ensure_dir(log_dir)

    # Split reports based on our new architecture
    report2 = report.pop("report2", {})
    merged_report = report.pop("merged_report", {})
    report1 = report # the rest is report 1

    report1_path = log_dir / "report1.json"
    report2_path = log_dir / "report2.json"
    report3_path = log_dir / "report3_merged.json"
    
    try:
        with open(report1_path, "w", encoding="utf-8") as f:
            json.dump(report1, f, indent=2, default=str)
        with open(report2_path, "w", encoding="utf-8") as f:
            json.dump(report2, f, indent=2, default=str)
        with open(report3_path, "w", encoding="utf-8") as f:
            json.dump(merged_report, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save JSON reports for {assessment_id}: {e}")

    # Generate training data explicitly
    training_data_path = log_dir / "training_data.jsonl"
    try:
        training_record = {
            "input_source": source_value,
            "report1_static": {k: v for k, v in report1.items() if k not in ["executive_summary", "blockers"]},
            "report2_ai": report2,
            "final_merged": merged_report,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(training_data_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(training_record, default=str) + "\n")
    except Exception as e:
        logger.error(f"Failed to save training_data.jsonl for {assessment_id}: {e}")

    summary_path = log_dir / "summary.txt"
    # Use merged report for text summary if available, else report1
    summary_data = merged_report if merged_report else report1
    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(_build_text_summary(assessment_id, user_id, source_value, source_type, score, status, summary_data))
    except Exception as e:
        logger.error(f"Failed to save summary.txt for {assessment_id}: {e}")

    meta_path = log_dir / "metadata.json"
    try:
        meta = {
            "assessment_id": assessment_id,
            "user_id":       user_id,
            "source":        source_value,
            "source_type":   source_type,
            "score":         score,
            "status":        status,
            "saved_at":      datetime.now(timezone.utc).isoformat(),
            "files": {
                "report1": str(report1_path),
                "report2": str(report2_path),
                "report3": str(report3_path),
                "training": str(training_data_path),
                "summary": str(summary_path),
            },
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save metadata.json for {assessment_id}: {e}")

    logger.info(f"Assessment log saved to {log_dir}")
    return log_dir

def _build_text_summary(
    assessment_id: str, user_id: str, source_value: str, source_type: str,
    score: int, status: str, report: dict,
) -> str:
    lines: list[str] = []
    sep = "=" * 70

    lines += [
        sep,
        "  APP READER — AI READINESS ASSESSMENT REPORT",
        sep,
        f"  Assessment ID : {assessment_id}",
        f"  User ID       : {user_id}",
        f"  Source        : {source_value} ({source_type})",
        f"  Generated     : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        sep,
        f"  OVERALL SCORE : {score}/100  [{status}]",
        sep, "",
    ]

    exec_sum = report.get("executive_summary", "")
    if exec_sum:
        lines += ["EXECUTIVE SUMMARY", "-" * 40, exec_sum, ""]

    blockers = report.get("blockers", [])
    if blockers:
        lines += ["⛔ HARD BLOCKERS (must fix before AI integration)", "-" * 40]
        for b in blockers:
            lines.append(f"  • {b}")
        lines.append("")

    layer_scores = report.get("layer_scores", {})
    if layer_scores:
        lines += ["LAYER SCORES", "-" * 40]
        for layer, s in sorted(layer_scores.items(), key=lambda x: x[1]):
            bar = "█" * (s // 10) + "░" * (10 - s // 10)
            flag = "✅" if s >= 70 else ("⚠️" if s >= 40 else "❌")
            lines.append(f"  {flag} {layer:<20} {bar}  {s:>3}/100")
        lines.append("")

    risks = report.get("risk_register", report.get("risks", []))
    if risks:
        lines += ["RISK REGISTER", "-" * 40]
        for r in risks[:10]:
            sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(r.get("severity",""), "⚪")
            lines.append(f"  {sev_icon} [{r.get('severity','?').upper()}] {r.get('name','Unknown')}")
            lines.append(f"     Category: {r.get('category','')}")
            locs = r.get("locations", [])
            for loc in locs[:3]:
                lines.append(f"     📍 {loc.get('file','')}:{loc.get('line','')} — {loc.get('snippet','')[:80]}")
            lines.append(f"     💡 {r.get('advice','')}")
            lines.append("")

    diags = report.get("improvement_diagnostics", [])
    if diags:
        lines += ["IMPROVEMENT PLAN", "-" * 40]
        for d in diags:
            lines.append(f"  {d.get('icon','📊')} {d.get('layer','')} — Score: {d.get('score','?')}/100 [{d.get('priority','?').upper()}] — Effort: {d.get('effort','?')}")
            lines.append(f"     {d.get('tip','')}")
            lines.append("")

    lines += [sep, "  END OF REPORT", sep]
    return "\n".join(lines)

def list_logs() -> list[dict]:
    """List all saved assessment logs by reading metadata.json files."""
    if not LOGS_ROOT.exists():
        return []
    logs = []
    for subdir in sorted(LOGS_ROOT.iterdir(), reverse=True):
        if not subdir.is_dir():
            continue
        meta_path = subdir / "metadata.json"
        if meta_path.exists():
            try:
                with open(meta_path, encoding="utf-8") as f:
                    logs.append(json.load(f))
            except Exception:
                pass
    return logs

def get_log_paths(assessment_id: str) -> dict | None:
    """Return file paths for a specific assessment log."""
    log_dir = LOGS_ROOT / assessment_id
    if not log_dir.exists():
        return None
    return {
        "dir":     str(log_dir),
        "report":  str(log_dir / "report.json"),
        "summary": str(log_dir / "summary.txt"),
        "meta":    str(log_dir / "metadata.json"),
    }
