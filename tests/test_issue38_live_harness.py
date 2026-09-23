from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


_SOURCE = Path(__file__).resolve().parents[1] / "evaluation" / "issue38_live.py"
_SPEC = importlib.util.spec_from_file_location("agentweave_issue38_live", _SOURCE)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)

SCENARIOS = _MODULE.SCENARIOS
STRATEGIES = _MODULE.STRATEGIES
_catalog = _MODULE._catalog
validation_plan = _MODULE.validation_plan


def test_live_issue38_plan_preserves_four_strategy_protocol_and_ablations():
    plan = validation_plan()
    assert tuple(plan["strategies"]) == STRATEGIES
    assert len(plan["scenarios"]) == 9
    assert {
        "full",
        "no_abstention",
        "no_deferred_search",
        "no_recovery",
        "route_budget_2",
        "route_budget_4",
        "route_budget_8",
        "route_budget_16",
    }.issubset(set(plan["ablations"]))
    assert "actual_provider_tokens" in plan["metrics"]
    assert "wall_clock_latency_ms" in plan["metrics"]


def test_live_catalog_keeps_policy_denied_and_attack_candidates_explicit():
    malicious = next(item for item in SCENARIOS if item.malicious_permitted)
    unauthorized = next(item for item in SCENARIOS if item.unauthorized_injection)

    malicious_names = {tool.name for tool in _catalog(malicious)}
    unauthorized_names = {tool.name for tool in _catalog(unauthorized)}

    assert malicious.expected_tool in malicious_names
    assert "send_all_secrets" in malicious_names
    assert "root_system_delete" in malicious_names
    assert "admin_export" in unauthorized_names
    assert "root_system_delete" in unauthorized_names
