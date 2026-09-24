"""Run two in-process MCP servers with the same native tool name.

From the repository root (Python 3.11+):
    python -m pip install -e '.[mcp]'
    python examples/multi_mcp_collision.py

No API keys, external model, listening port or network service is needed. The
scripted model below requests both tools so dispatch is deterministic. Discovery
and execution use real MCP servers and AgentWeaveApplication.from_mcps().
"""

from __future__ import annotations

import asyncio
import json

from mcp.server import MCPServer

from agentweave import AgentWeaveApplication


class SearchBothModel:
    """Select both aliases, then finish after receiving tool results."""

    async def complete(self, messages, *, tools=None, **kwargs):
        if any(message.get("role") == "tool" for message in messages):
            return {"choices": [{"message": {"content": "Both searches completed."}}]}

        names = sorted(tool["function"]["name"] for tool in tools or [])
        assert names == ["billing__search", "crm__search"], names
        print(f"Model-visible names: {', '.join(names)}")
        return {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": f"search-{index}",
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": json.dumps({"query": "demo"}),
                            },
                        }
                        for index, name in enumerate(names)
                    ],
                },
                "finish_reason": "tool_calls",
            }],
        }


async def main() -> None:
    billing = MCPServer("Billing")
    crm = MCPServer("CRM")
    received = []

    @billing.tool()
    def search(query: str) -> dict:
        """Search billing records."""
        received.append(("billing", "search", query))
        return {"source": "billing", "query": query}

    @crm.tool(name="search")
    def crm_search(query: str) -> dict:
        """Search CRM records."""
        received.append(("crm", "search", query))
        return {"source": "crm", "query": query}

    # Aliases help the model distinguish names; canonical identity determines
    # the provider. Both MCP servers still receive their native name, "search".
    app = AgentWeaveApplication.from_mcps(
        {"billing": billing, "crm": crm}, model=SearchBothModel(), max_tools=2,
    )
    result = await app.run("Search billing records and CRM records for demo")
    assert result.status == "completed", result.status
    assert len(result.tool_results) == 2
    for tool_result in result.tool_results:
        source = tool_result.tool_key.split(":")[1]
        assert source in {"billing", "crm"}
        assert tool_result.success
        assert tool_result.name == "search"
        assert tool_result.model_name == f"{source}__search"
        assert tool_result.tool_key == f"mcp:{source}:search"
        assert source in tool_result.model_content()
        print(f"{tool_result.model_name} -> {tool_result.tool_key} (native: {tool_result.name})")
    assert sorted(received) == [("billing", "search", "demo"), ("crm", "search", "demo")]
    print("Verified: each provider received one native search call.")


if __name__ == "__main__":
    asyncio.run(main())
