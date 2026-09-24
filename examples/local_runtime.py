"""Route and execute local tools without a model service or optional integrations.

From the repository root: python examples/local_runtime.py
Install first with: python -m pip install -e '.[dev]'
"""

from __future__ import annotations

import asyncio

from agentweave import (
    AgentWeaveRuntime,
    CallableExecutor,
    ModelResponse,
    RuntimeResult,
    StaticToolCatalog,
    ToolCall,
    ToolSpec,
)


class ScriptedModel:
    """A fixed two-turn demonstration, not a language model or a general parser."""

    async def complete(self, messages, *, tools=None, **kwargs):
        if messages[-1]["role"] == "tool":
            return ModelResponse(text=f"Result: {messages[-1]['content']}")
        names = [tool["function"]["name"] for tool in tools or []]
        print("Model-visible tools:", ", ".join(names))
        if "add_numbers" not in names:
            return ModelResponse(text="The addition tool was not routed.")
        return ModelResponse(tool_calls=(
            ToolCall(name="add_numbers", arguments={"a": 19, "b": 23}, id="sum-1"),
        ))


async def main() -> RuntimeResult:
    text_schema = {
        "type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"],
    }
    tools = [
        ToolSpec(
            name="add_numbers", description="Add two numbers and return their sum.",
            input_schema={
                "type": "object",
                "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                "required": ["a", "b"],
            },
        ),
        ToolSpec(name="uppercase", description="Convert text to uppercase.", input_schema=text_schema),
        ToolSpec(name="count_words", description="Count words in text.", input_schema=text_schema),
    ]
    runtime = AgentWeaveRuntime(
        model=ScriptedModel(),
        catalog=StaticToolCatalog(tools),
        executor=CallableExecutor({
            "add_numbers": lambda a, b: a + b,
            "uppercase": lambda text: text.upper(),
            "count_words": lambda text: len(text.split()),
        }),
        max_tools=1,
    )
    task = "Add the numbers 19 and 23 and return their sum."
    async with runtime:
        preview = await runtime.preview_route(task)
        print("Catalog tools:", ", ".join(tool.name for tool in tools))
        print("Routed tools:", ", ".join(tool.name for tool in preview.selected))
        result = await runtime.run(task)
        print("Status:", result.status)
        print(result.response.text if result.response else "No response")
        return result


if __name__ == "__main__":
    asyncio.run(main())
