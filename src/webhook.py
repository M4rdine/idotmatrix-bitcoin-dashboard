"""FastAPI webhook server for receiving agent status updates.

Runs as a background task alongside the main display loop.
Other systems POST status updates to /api/agents/status.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.data.agents import AgentStatusPayload, AgentStore


logger = logging.getLogger(__name__)

app = FastAPI(title="LED Matrix Dashboard Webhook", version="0.1.0")


class HealthResponse(BaseModel):
    status: str
    agents_count: int


class AgentResponse(BaseModel):
    name: str
    status: str
    message: str


class AgentListResponse(BaseModel):
    agents: list[AgentResponse]
    count: int


@app.get("/health")
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    store = AgentStore.get_instance()
    return HealthResponse(status="ok", agents_count=store.count)


@app.post("/api/agents/status", status_code=201)
async def update_agent_status(payload: AgentStatusPayload) -> AgentResponse:
    """Receive an agent status update.

    Example POST body:
    {
        "name": "trading-bot",
        "status": "online",
        "message": "Running smoothly"
    }

    Valid statuses: online, offline, error, warning, degraded, running, ok, unknown
    """
    valid_statuses = {
        "online", "offline", "error", "warning",
        "degraded", "running", "ok", "unknown",
    }
    if payload.status.lower() not in valid_statuses:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{payload.status}'. Must be one of: {sorted(valid_statuses)}",
        )

    store = AgentStore.get_instance()
    agent = store.update(
        name=payload.name,
        status=payload.status.lower(),
        message=payload.message,
    )
    logger.info("Agent status updated: %s -> %s", agent.name, agent.status)
    return AgentResponse(name=agent.name, status=agent.status, message=agent.message)


@app.get("/api/agents")
async def list_agents() -> AgentListResponse:
    """List all tracked agent statuses."""
    store = AgentStore.get_instance()
    agents = store.get_all()
    return AgentListResponse(
        agents=[
            AgentResponse(name=a.name, status=a.status, message=a.message)
            for a in agents
        ],
        count=len(agents),
    )


@app.delete("/api/agents/{name}", status_code=204)
async def remove_agent(name: str) -> None:
    """Remove an agent from tracking."""
    store = AgentStore.get_instance()
    if not store.remove(name):
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
