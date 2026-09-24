import socket

import pytest

from examples.local_runtime import main


@pytest.mark.asyncio
async def test_local_runtime_example_executes_without_network(monkeypatch, capsys):
    def unexpected_connection(*args, **kwargs):
        raise AssertionError("The local runtime example must not connect to a service")

    monkeypatch.setattr(socket.socket, "connect", unexpected_connection)
    result = await main()

    assert result.status == "completed"
    assert len(result.tool_results) == 1
    assert result.tool_results[0].name == "add_numbers"
    assert result.tool_results[0].success
    assert result.tool_results[0].content == 42
    assert result.response.text == "Result: 42"
    output = capsys.readouterr().out
    assert "Catalog tools: add_numbers, uppercase, count_words" in output
    assert "Routed tools: add_numbers\n" in output
    assert "Model-visible tools: add_numbers\n" in output
