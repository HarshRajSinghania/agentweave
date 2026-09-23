import sqlite3

import pytest

from agentweave.models import AgentProfile, Capability
from agentweave.persistence import ReputationStore


def test_file_connections_close_after_success_and_failure(tmp_path, monkeypatch):
    connections = []
    connect = sqlite3.connect

    def tracked_connect(*args, **kwargs):
        connection = connect(*args, **kwargs)
        connections.append(connection)  # Prevent garbage collection from hiding leaks.
        return connection

    monkeypatch.setattr(sqlite3, "connect", tracked_connect)
    database = tmp_path / "reputation.db"
    store = ReputationStore(database)
    agent = AgentProfile("demo", "Demo", [Capability("analysis")])
    store.save_agent(agent)
    store.record_outcome("demo", True, 0.9, {"phase": "test"})
    store.save_workflow_checkpoint("workflow", {"step": 1})
    assert store.load_agents()[0].agent_id == "demo"
    assert store.recent_outcomes("demo")[0]["success"]
    assert store.load_workflow_checkpoint("workflow") == {"step": 1}
    assert store.list_workflow_checkpoints() == [{"step": 1}]
    assert store.delete_workflow_checkpoint("workflow")
    with pytest.raises(TypeError):
        store.record_outcome("demo", False, detail={"invalid": object()})
    assert len(store.recent_outcomes("demo")) == 1
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("select 1")
    database.unlink()  # Must also work on Windows while the store is alive.


def test_memory_store_retains_data_across_operations():
    store = ReputationStore(":memory:")
    store.save_workflow_checkpoint("workflow", {"step": 1})
    assert store.load_workflow_checkpoint("workflow") == {"step": 1}
    store.record_outcome("demo", True)
    assert store.recent_outcomes("demo")[0]["success"]
    store._memory_conn.close()
