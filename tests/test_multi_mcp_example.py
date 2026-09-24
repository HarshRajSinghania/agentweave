from pathlib import Path
import runpy

import pytest

pytest.importorskip("mcp")


@pytest.mark.asyncio
async def test_multi_mcp_collision_example_dispatches_to_both_servers(capsys):
    example = Path(__file__).resolve().parents[1] / "examples" / "multi_mcp_collision.py"
    namespace = runpy.run_path(str(example))
    await namespace["main"]()
    output = capsys.readouterr().out
    assert "Model-visible names: billing__search, crm__search" in output
    assert "billing__search -> mcp:billing:search (native: search)" in output
    assert "crm__search -> mcp:crm:search (native: search)" in output
    assert "Verified: each provider received one native search call." in output
