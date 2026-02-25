"""
Analytics — cost breakdown aggregation from events.jsonl.
Extracted from server.py to keep server.py focused on HTTP/WebSocket routing.
"""

import json
import pathlib
from typing import Any, Dict


def cost_breakdown(events_path: pathlib.Path) -> Dict[str, Any]:
    """Aggregate llm_usage events into cost breakdown dicts."""
    by_model: Dict[str, Dict[str, Any]] = {}
    by_api_key: Dict[str, Dict[str, Any]] = {}
    by_model_category: Dict[str, Dict[str, Any]] = {}
    by_task_category: Dict[str, Dict[str, Any]] = {}
    total_cost = 0.0
    total_calls = 0

    def _acc(d: Dict, key: str) -> Dict:
        if key not in d:
            d[key] = {"cost": 0.0, "calls": 0}
        return d[key]

    try:
        if events_path.exists():
            with events_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        evt = json.loads(line)
                    except Exception:
                        continue
                    if evt.get("type") != "llm_usage":
                        continue
                    cost = float(evt.get("cost") or 0)
                    model = str(evt.get("model") or "unknown")
                    api_key_type = str(
                        evt.get("api_key_type") or evt.get("provider") or "openrouter"
                    )
                    model_cat = str(evt.get("model_category") or "other")
                    task_cat = str(evt.get("category") or "task")

                    total_cost += cost
                    total_calls += 1

                    _acc(by_model, model)["cost"] += cost
                    _acc(by_model, model)["calls"] += 1
                    _acc(by_api_key, api_key_type)["cost"] += cost
                    _acc(by_api_key, api_key_type)["calls"] += 1
                    _acc(by_model_category, model_cat)["cost"] += cost
                    _acc(by_model_category, model_cat)["calls"] += 1
                    _acc(by_task_category, task_cat)["cost"] += cost
                    _acc(by_task_category, task_cat)["calls"] += 1
    except Exception:
        pass

    def _sorted(d: Dict) -> Dict:
        return dict(sorted(d.items(), key=lambda x: x[1]["cost"], reverse=True))

    return {
        "total_cost": round(total_cost, 4),
        "total_calls": total_calls,
        "by_model": _sorted(by_model),
        "by_api_key": _sorted(by_api_key),
        "by_model_category": _sorted(by_model_category),
        "by_task_category": _sorted(by_task_category),
    }
