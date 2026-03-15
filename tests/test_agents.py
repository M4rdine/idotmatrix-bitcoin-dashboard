"""Tests for agent status store."""

from __future__ import annotations

import pytest

from src.data.agents import AgentStatus, AgentStore


@pytest.fixture(autouse=True)
def reset_store() -> None:
    """Reset the singleton store before each test."""
    AgentStore.reset_instance()


class TestAgentStatus:
    def test_agent_status_creation(self) -> None:
        agent = AgentStatus(name="bot-1", status="online")
        assert agent.name == "bot-1"
        assert agent.status == "online"
        assert agent.message == ""

    def test_agent_status_with_message(self) -> None:
        agent = AgentStatus(name="bot-1", status="error", message="Connection timeout")
        assert agent.message == "Connection timeout"

    def test_agent_status_has_timestamp(self) -> None:
        agent = AgentStatus(name="bot-1", status="online")
        assert agent.last_seen is not None

    def test_agent_status_is_immutable(self) -> None:
        agent = AgentStatus(name="bot-1", status="online")
        with pytest.raises(AttributeError):
            agent.status = "offline"  # type: ignore[misc]


class TestAgentStore:
    def test_singleton(self) -> None:
        store1 = AgentStore.get_instance()
        store2 = AgentStore.get_instance()
        assert store1 is store2

    def test_update_creates_agent(self) -> None:
        store = AgentStore.get_instance()
        agent = store.update("bot-1", "online")
        assert agent.name == "bot-1"
        assert agent.status == "online"
        assert store.count == 1

    def test_update_replaces_agent(self) -> None:
        store = AgentStore.get_instance()
        store.update("bot-1", "online")
        store.update("bot-1", "error", "Failed")
        assert store.count == 1
        agent = store.get("bot-1")
        assert agent is not None
        assert agent.status == "error"
        assert agent.message == "Failed"

    def test_get_nonexistent(self) -> None:
        store = AgentStore.get_instance()
        assert store.get("nonexistent") is None

    def test_get_all_sorted(self) -> None:
        store = AgentStore.get_instance()
        store.update("charlie", "online")
        store.update("alice", "online")
        store.update("bob", "online")
        agents = store.get_all()
        assert [a.name for a in agents] == ["alice", "bob", "charlie"]

    def test_remove_existing(self) -> None:
        store = AgentStore.get_instance()
        store.update("bot-1", "online")
        removed = store.remove("bot-1")
        assert removed is True
        assert store.count == 0

    def test_remove_nonexistent(self) -> None:
        store = AgentStore.get_instance()
        removed = store.remove("nonexistent")
        assert removed is False

    def test_multiple_agents(self) -> None:
        store = AgentStore.get_instance()
        store.update("bot-1", "online")
        store.update("bot-2", "error")
        store.update("bot-3", "warning")
        assert store.count == 3

    def test_update_does_not_mutate(self) -> None:
        """Verify that updating an agent creates a new object."""
        store = AgentStore.get_instance()
        agent_v1 = store.update("bot-1", "online")
        agent_v2 = store.update("bot-1", "error")
        # Original object is unchanged
        assert agent_v1.status == "online"
        assert agent_v2.status == "error"
        assert agent_v1 is not agent_v2
