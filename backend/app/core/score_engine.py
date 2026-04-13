"""
score_engine.py — Fuse all 9 analysis layers into a final score + status.
"""

LAYER_WEIGHTS = {
    "static_rules":   30,
    "import_graph":   15,
    "ast_metrics":    10,
    "dependencies":   10,
    "test_coverage":  10,
    "api_quality":    8,
    "tech_debt":      7,
    "env_maturity":   5,
    "observability":  5,
}

HARD_BLOCKERS = [
    "hardcoded_secrets",
    "no_auth",
    "critical_vulnerability",
]

def compute_static_score(rules: dict) -> dict:
    """Convert 25 rule results into a 0-100 score."""
    positive_weight = 0
    positive_earned = 0
    risks = []

    for rule_id, result in rules.items():
        w = result["weight"]
        if w > 0:
            positive_weight += w
            if result["found"]:
                positive_earned += w
        else:

            if result["found"]:
                risks.append({
                    "rule_id": rule_id,
                    "name": result["name"],
                    "severity": result["severity"],
                    "category": result["category"],
                    "penalty": abs(w),
                })

    base = int((positive_earned / max(positive_weight, 1)) * 100)
    penalty = sum(r["penalty"] for r in risks)
    score = max(0, min(100, base - penalty))

    has_hardcoded = rules.get("R11", {}).get("found", False)
    has_auth = rules.get("R01", {}).get("found", False) or rules.get("R02", {}).get("found", False)
    has_eval = rules.get("R18", {}).get("found", False)

    blockers = []
    if has_hardcoded:
        blockers.append("Hardcoded secrets detected — critical security failure")
    if not has_auth:
        blockers.append("No authentication detected (JWT/OAuth) — AI integration blocked")
    if has_eval:
        blockers.append("Dangerous eval/exec usage found — code execution risk")

    return {
        "static_score": score,
        "positive_earned": positive_earned,
        "positive_weight": positive_weight,
        "risks": risks,
        "blockers": blockers,
        "has_blockers": len(blockers) > 0,
    }

def fuse_scores(
    static: dict,
    graph: dict,
    ast: dict,
    deps: dict,
    tests: dict,
    api: dict,
    debt: dict,
    env: dict,
    obs: dict,
    project_info: dict,
) -> dict:
    cat_scores = static.get("category_scores", {})
    
    # Safely get a category score, defaulting to the overall static_score
    def _cget(name: str) -> int:
        return cat_scores.get(name, static.get("static_score", 0))

    layer_scores = {
        "security":        _cget("Security & Auth"),
        "data_protection": _cget("Data Protection"),
        "api_quality":     int((_cget("API Quality") + api.get("api_score", 0)) / 2),
        "infrastructure":  int((_cget("Infrastructure") + deps.get("dependency_score", 0) + env.get("env_score", 0)) / 3),
        "code_quality":    int((_cget("Code Quality") + ast.get("ast_score", 0) + tests.get("test_score", 0) + debt.get("debt_score", 0)) / 4),
        "ai_ml_readiness": _cget("AI/ML Readiness"),
        "performance":     _cget("Performance"),
        "compliance":      int((_cget("Compliance") + obs.get("observability_score", 0)) / 2),
        "architecture":    graph.get("cohesion_score", 0),
    }

    # Recalculate raw score as the simple average of all 9 layers
    raw_score = int(sum(layer_scores.values()) / 9)

    lang_diversity = project_info.get("language_diversity", 1)
    if lang_diversity > 4:
        raw_score = max(0, raw_score - 5)

    has_blockers = bool(static.get("has_blockers", bool(static.get("blockers", []))))
    if has_blockers:
        raw_score = min(raw_score, 49)

    score = max(0, min(100, raw_score))

    if score >= 75:
        status = "Strong"
    elif score >= 50:
        status = "Moderate"
    elif score >= 30:
        status = "Weak"
    else:
        status = "Critical"

    gate = {
        "score_ok": score >= 80,
        "no_blockers": not has_blockers,
        "has_tests": tests["test_ratio"] >= 0.1,
        "has_auth": True,
        "no_hardcoded_secrets": not project_info.get("has_hardcoded_secrets", False),
    }
    passed_gates = sum(gate.values())
    why_not_80 = _build_why_not_80(score, layer_scores, static, tests, gate)

    return {
        "score": score,
        "status": status,
        "layer_scores": layer_scores,
        "layer_weights": LAYER_WEIGHTS,
        "risks":    static.get("risks", []),
        "blockers": static.get("blockers", []),
        "has_blockers": has_blockers,
        "gate_checks": gate,
        "gates_passed": passed_gates,
        "why_not_80": why_not_80,
    }

def _build_why_not_80(score, layers, static, tests, gate) -> list[str]:
    tips = []
    if score >= 80:
        return ["🎉 Project is AI-ready! Excellent readiness score."]

    sorted_layers = sorted(layers.items(), key=lambda x: x[1])
    for name, val in sorted_layers[:3]:
        if val < 60:
            tips.append(f"Improve {name.replace('_', ' ').title()} (currently {val}/100)")

    if static.get("has_blockers", bool(static.get("blockers", []))):
        for b in static.get("blockers", []):
            tips.append(f"⛔ Fix blocker: {b}")

    if tests["test_ratio"] < 0.1:
        tips.append("Add unit tests — test:source ratio is below 10%")

    if not gate["score_ok"]:
        needed = 80 - score
        tips.append(f"Need {needed} more points to reach AI-ready threshold")

    return tips[:6]
