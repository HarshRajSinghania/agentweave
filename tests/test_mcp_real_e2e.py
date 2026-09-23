from __future__ import annotations

import pytest

pytest.importorskip("mcp")

from mcp.server import MCPServer

from agentweave import AgentWeaveApplication, RunContext


class SelectingModel:
    def __init__(self, preferred_prefix: str | None = None):
        self.preferred_prefix = preferred_prefix
        self.calls = 0

    async def complete(self, messages, *, tools=None, **kwargs):
        self.calls += 1
        if messages and messages[-1].get("role") == "tool":
            return {
                "choices": [
                    {
                        "message": {"content": "done", "tool_calls": []},
                        "finish_reason": "stop",
                    }
                ]
            }
        choices = list(tools or [])
        assert choices
        selected = choices[0]
        if self.preferred_prefix:
            selected = next(
                tool
                for tool in choices
                if tool["function"]["name"].startswith(self.preferred_prefix)
            )
        name = selected["function"]["name"]
        properties = selected["function"]["parameters"].get("properties", {})
        arguments = {}
        for key, spec in properties.items():
            kind = spec.get("type")
            arguments[key] = 7 if kind in {"integer", "number"} else "INV-7"
        import json

        return {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": f"call-{self.calls}",
                                "type": "function",
                                "function": {
                                    "name": name,
                                    "arguments": json.dumps(arguments),
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }


@pytest.mark.asyncio
async def test_real_mcp_server_lists_routes_and_executes_through_runtime():
    server = MCPServer("AgentWeaveE2E")

    @server.tool()
    def lookup_invoice(invoice_id: str) -> dict:
        """Look up one invoice by id."""
        return {"invoice_id": invoice_id, "status": "paid"}

    app = AgentWeaveApplication.from_mcp(
        server,
        model=SelectingModel(),
        source="billing",
        max_tools=4,
    )
    result = await app.run(
        "look up invoice INV-7",
        context=RunContext(),
    )

    assert result.status == "completed"
    assert len(result.tool_results) == 1
    tool_result = result.tool_results[0]
    assert tool_result.success is True
    assert tool_result.name == "lookup_invoice"
    assert tool_result.tool_key == "mcp:billing:lookup_invoice"
    assert "paid" in tool_result.model_content()


@pytest.mark.asyncio
async def test_two_real_mcp_servers_with_same_native_name_dispatch_by_tool_identity():
    billing = MCPServer("Billing")
    crm = MCPServer("CRM")

    @billing.tool()
    def search(query: str) -> dict:
        """Search billing invoices."""
        return {"source": "billing", "query": query}

    @crm.tool(name="search")
    def crm_search(query: str) -> dict:
        """Search CRM contacts."""
        return {"source": "crm", "query": query}

    app = AgentWeaveApplication.from_mcps(
        {"billing": billing, "crm": crm},
        model=SelectingModel(preferred_prefix="billing__"),
        max_tools=8,
    )
    result = await app.run("billing search for INV-7")

    assert result.status == "completed"
    assert len(result.tool_results) == 1
    tool_result = result.tool_results[0]
    assert tool_result.success is True
    assert tool_result.name == "search"
    assert tool_result.model_name == "billing__search"
    assert tool_result.tool_key == "mcp:billing:search"
    assert "billing" in tool_result.model_content()
