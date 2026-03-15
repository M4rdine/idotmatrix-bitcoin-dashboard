"""Agent status tracking with in-memory store and webhook receiver.

Other systems POST status updates to the webhook endpoint,
which are stored in memory and displayed on the LED matrix.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar

from pydantic import BaseModel


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentStatus:
    """Immutable snapshot of an agent's status."""

    name: str
    status: str  # "online", "offline", "error", "warning", "degraded"
    message: str = ""
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AgentStatusPayload(BaseModel):
    """Pydantic model for incoming webhook payloads."""

    name: str
    status: str
    message: str = ""


class AgentStore:
    """Thread-safe in-memory store for agent statuses.

    Uses a dict keyed by agent name. Each update creates a new
    immutable AgentStatus (no mutation of existing objects).
    """

    _instance: ClassVar[AgentStore | None] = None

    def __init__(self) -> None:
        self._agents: dict[str, AgentStatus] = {}

    @classmethod
    def get_instance(cls) -> AgentStore:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton (for testing)."""
        cls._instance = None

    def update(self, name: str, status: str, message: str = "") -> AgentStatus:
        """Record a new status for an agent.

        Creates a new immutable AgentStatus and replaces the old one
        in the store (no mutation).
        """
        agent = AgentStatus(
            name=name,
            status=status,
            message=message,
            last_seen=datetime.now(timezone.utc),
        )
        self._agents = {**self._agents, name: agent}
        logger.info("Agent '%s' updated: %s", name, status)
        return agent

    def get(self, name: str) -> AgentStatus | None:
        """Get the current status of an agent."""
        return self._agents.get(name)

    def get_all(self) -> list[AgentStatus]:
        """Get all agent statuses, sorted by name."""
        return sorted(self._agents.values(), key=lambda a: a.name)

    def remove(self, name: str) -> bool:
        """Remove an agent from the store."""
        if name in self._agents:
            self._agents = {k: v for k, v in self._agents.items() if k != name}
            logger.info("Agent '%s' removed", name)
            return True
        return False

    @property
    def count(self) -> int:
        return len(self._agents)
