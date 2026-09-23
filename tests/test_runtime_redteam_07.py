from __future__ import annotations

import json

import pytest

from agentweave import (
    AgentWeaveRuntime,
    RunContext,
    StaticToolCatalog,
    ToolResult,
    ToolSpec,
)
from agentweave_security.authorization import AuthorizationDecision
from agentweave_byom import ToolRoutingResult


class FirstRouter:
    version = "redteam-first"

    async def aroute(self, text, tools, *, max_tools=8):
        return ToolRoutingResult(
            selected=list(tools[:max_tools]),
            filtered=list(tools[max_tools:]),
            provenance={"router": self.version},
            confidence=1.0,
            abstained=False,
        )


class OneCallModel:
    def __init__(self, name: str, arguments):
        self.name = name
        self.arguments = arguments

    async def complete(self, messages, *, tools=None, **kwargs):
        if messages and messages[-1].get("role") == "tool":
            return {"choices": [{"message": {"content": "done", "tool_calls": []}}]}
        arguments = self.arguments
        if not isinstance(arguments, str):
            arguments = json.dumps(arguments)
        return {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "attack-call",
                                "type": "function",
                                "function": {"name": self.name, "arguments": arguments},
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }


class CountingExecutor:
    def __init__(self):
        self.calls = 0

    async def execute(self, call, context):
        self.calls += 1
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            model_name=call.model_name,
            tool_key=call.tool_key,
            success=True,
            content="executed",
        )


class AmountPolicy:
    async def authorize_tool(self, *, call, tool, context):
        amount = int(call.arguments.get("amount", 0))
        if amount > 1000:
            return AuthorizationDecision(False, "amount-limit-exceeded")
        return AuthorizationDecision(True, "allowed")


@pytest.mark.asyncio
async def test_argument_escalation_is_denied_after_model_selection_before_execution():
    executor = CountingExecutor()
    runtime = AgentWeaveRuntime(
        model=OneCallModel("transfer", {"amount": 50000, "account": "A-1"}),
        catalog=StaticToolCatalog(
            [
                ToolSpec(
                    id="payments:transfer",
                    name="transfer",
                    description="transfer funds",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "amount": {"type": "integer", "minimum": 1},
                            "account": {"type": "string"},
                        },
                        "required": ["amount", "account"],
                        "additionalProperties": False,
                    },
                )
            ]
        ),
        executor=executor,
        router=FirstRouter(),
        authorization_policy=AmountPolicy(),
        max_recovery_attempts=0,
    )
    result = await runtime.run("transfer funds")

    assert result.status == "needs-review"
    assert executor.calls == 0
    assert result.tool_results[0].error == "authorization-denied:amount-limit-exceeded"


@pytest.mark.asyncio
async def test_invalid_json_is_rejected_before_authorization_and_execution():
    executor = CountingExecutor()
    runtime = AgentWeaveRuntime(
        model=OneCallModel("lookup", '{"id":'),
        catalog=StaticToolCatalog(
            [ToolSpec(name="lookup", input_schema={"type": "object"})]
        ),
        executor=executor,
        router=FirstRouter(),
        max_recovery_attempts=0,
    )
    result = await runtime.run("lookup")

    assert result.status == "needs-review"
    assert executor.calls == 0
    assert result.tool_results[0].error.startswith("invalid-tool-call:invalid-json:")


@pytest.mark.asyncio
async def test_malformed_or_hostile_tool_schema_fails_closed_before_executor():
    executor = CountingExecutor()
    runtime = AgentWeaveRuntime(
        model=OneCallModel("unsafe_schema", {"value": "x"}),
        catalog=StaticToolCatalog(
            [
                ToolSpec(
                    name="unsafe_schema",
                    input_schema={"type": "object", "properties": {"value": {"type": 7}}},
                )
            ]
        ),
        executor=executor,
        router=FirstRouter(),
        max_recovery_attempts=0,
    )
    result = await runtime.run("use unsafe schema")

    assert result.status == "needs-review"
    assert executor.calls == 0
    assert result.tool_results[0].error.startswith("invalid-tool-call:invalid-tool-schema:")


@pytest.mark.asyncio
async def test_model_cannot_switch_to_unexposed_high_risk_tool_by_name():
    executor = CountingExecutor()
    runtime = AgentWeaveRuntime(
        model=OneCallModel("admin_delete", {}),
        catalog=StaticToolCatalog(
            [
                ToolSpec(name="read", description="read only"),
                ToolSpec(
                    name="admin_delete",
                    description="delete records",
                    permissions=frozenset({"admin"}),
                    risk_level="critical",
                ),
            ]
        ),
        executor=executor,
        router=FirstRouter(),
        max_recovery_attempts=0,
    )
    result = await runtime.run("read records", context=RunContext())

    assert result.status == "needs-review"
    assert executor.calls == 0
    assert result.tool_results[0].error == "authorization-denied:tool-not-model-visible"
