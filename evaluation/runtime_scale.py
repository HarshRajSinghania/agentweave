from __future__ import annotations

import argparse
import json
import time
import tracemalloc
from pathlib import Path

from agentweave import ToolSpec
from agentweave_byom import DeterministicRouterV1


def _catalog(size: int) -> list[ToolSpec]:
    if size < 2:
        raise ValueError("catalog size must be at least 2")
    tools = [
        ToolSpec(
            id=f"scale:noise:{index}",
            name=f"noise_tool_{index}",
            description=f"generic unrelated operation number {index}",
            input_schema={"type": "object", "properties": {}},
        )
        for index in range(size - 1)
    ]
    tools.append(
        ToolSpec(
            id="scale:target",
            name="customer_invoice_lookup",
            description="find a customer invoice by invoice identifier",
            input_schema={
                "type": "object",
                "properties": {"invoice_id": {"type": "string"}},
            },
        )
    )
    return tools


def run_case(size: int, budget: int) -> dict:
    tools = _catalog(size)
    descriptors = [tool.to_function_tool() for tool in tools]
    router = DeterministicRouterV1()
    query = "find customer invoice by invoice identifier"

    tracemalloc.start()
    start = time.perf_counter()
    result = router.route(query, descriptors, max_tools=budget)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    selected = [item["function"]["name"] for item in result.selected]
    return {
        "catalog_size": size,
        "route_budget": budget,
        "selected_count": len(selected),
        "target_selected": "customer_invoice_lookup" in selected,
        "candidate_reduction": 1.0 - len(selected) / size,
        "latency_ms": elapsed_ms,
        "peak_memory_bytes": peak,
        "routing_confidence": result.confidence,
        "selected_tools": selected,
    }


def run_benchmark(sizes: list[int], budgets: list[int]) -> dict:
    rows = [run_case(size, budget) for size in sizes for budget in budgets]
    return {
        "protocol": "agentweave-routing-scale-v1",
        "evidence_boundary": {
            "router": "DeterministicRouterV1",
            "latency": "wall-clock on the executing host; not a universal performance claim",
            "memory": "Python tracemalloc peak for the measured routing call",
            "production_claim": False,
        },
        "rows": rows,
        "all_targets_selected": all(row["target_selected"] for row in rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="100,1000,10000,100000")
    parser.add_argument("--budgets", default="8")
    parser.add_argument("--output", default="runtime-scale-results.json")
    args = parser.parse_args()
    sizes = [int(value) for value in args.sizes.split(",") if value.strip()]
    budgets = [int(value) for value in args.budgets.split(",") if value.strip()]
    payload = run_benchmark(sizes, budgets)
    if not payload["all_targets_selected"]:
        raise SystemExit("target tool was not selected in one or more scale cases")
    Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
