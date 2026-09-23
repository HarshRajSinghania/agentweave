# AgentWeave 0.7 quickstart

The shortest supported path is an application around an MCP server plus a model adapter.

```bash
pip install 'agentweave-router[mcp]'
```

```python
import asyncio

from agentweave import AgentWeaveApplication
from agentweave_byom import OpenAICompatibleModelAdapter

model = OpenAICompatibleModelAdapter(
    model='my-model',
    base_url='https://model.example/v1',
    api_key='...',
)

app = AgentWeaveApplication.from_mcp(
    'https://tools.example/mcp',
    model=model,
    max_tools=8,
)

async def main():
    result = await app.run('Find invoice INV-7')
    print(result.response.text if result.response else result.status)

asyncio.run(main())
```

`AgentWeaveApplication` owns the MCP connection, runtime lifecycle, plugin lifecycle, routing, authorization, execution, recovery, and telemetry.

## Several MCP servers

Use logical source names when a runtime can reach more than one MCP server:

```python
app = AgentWeaveApplication.from_mcps(
    {
        'billing': 'https://billing.example/mcp',
        'crm': 'https://crm.example/mcp',
    },
    model=model,
)
```

If both servers expose a native tool called `search`, AgentWeave exposes collision-safe names such as `billing__search` and `crm__search` to the model. The MCP calls still use the native `search` name and execution is dispatched by the canonical tool identity (`mcp:billing:search` versus `mcp:crm:search`).

## Security ordering

Every normal run follows the same order:

```text
catalog
  -> deterministic scope
  -> routing
  -> model
  -> JSON Schema validation
  -> argument-aware authorization
  -> executor
  -> bounded recovery / rediscovery
```

A tool selected by the model does not receive execution permission merely because it was routed. Calls are resolved back to an exact `ToolSpec`, validated, authorized, and only then executed.

## Advanced composition

The lower-level helpers remain available when an application needs direct control:

```python
from agentweave import mcp_runtime, multi_mcp_runtime

runtime = mcp_runtime('https://tools.example/mcp', model=model)
```

For custom catalogs, executors, routers, policies, model adapters, or plugin components, use `AgentWeaveRuntime`, `AgentWeaveBuilder`, or `RuntimeFactory`.
