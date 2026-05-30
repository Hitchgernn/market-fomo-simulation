"""FastAPI entry point for the FOMO market simulation backend."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.engine.model import StockMarketModel
from backend.llm.rotator import AgentChatRotator


STATE_COLORS = {
    "N": "#22c55e",
    "A": "#eab308",
    "P": "#ef4444",
}


def _read_api_keys() -> list[str]:
    raw_keys = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or ""
    return [key.strip() for key in raw_keys.split(",") if key.strip()]


def _build_chat_rotator() -> AgentChatRotator | None:
    api_keys = _read_api_keys()
    if not api_keys:
        return None
    return AgentChatRotator(api_keys=api_keys)


def create_model() -> StockMarketModel:
    """Create the long-lived simulation model used by the API process."""
    return StockMarketModel(chat_rotator=_build_chat_rotator())


model = create_model()
app = FastAPI(title="FOMO Market Simulation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/tick")
def tick() -> dict[str, Any]:
    """Advance the simulation by one tick and return frontend-ready JSON."""
    model.step()
    return {
        "tick": model.steps,
        "price": {
            "current": model.current_price,
            "base": model.base_price,
            "araLimit": model.ara_limit,
            "arbLimit": model.arb_limit,
            "araTriggered": model.ara_triggered,
            "arbTriggered": model.arb_triggered,
        },
        "orderBook": {
            "buyVolume": model.last_buy_volume,
            "sellVolume": model.last_sell_volume,
            "imbalance": model.last_order_imbalance,
        },
        "nodes": _serialize_nodes(model),
        "chats": [
            {
                "agentId": chat.agent_id,
                "message": chat.message,
            }
            for chat in model.chats
        ],
    }


def _serialize_nodes(stock_model: StockMarketModel) -> list[dict[str, Any]]:
    node_to_agent_id = _node_to_agent_id(stock_model)
    nodes: list[dict[str, Any]] = []

    for node_id, agents in stock_model.agents_by_node:
        if not agents:
            continue

        agent = agents[0]
        state = getattr(agent, "state", "N")
        neighbor_ids = [
            node_to_agent_id[neighbor_node]
            for neighbor_node in stock_model.grid.G.neighbors(node_id)
            if neighbor_node in node_to_agent_id
        ]

        nodes.append(
            {
                "id": int(agent.unique_id),
                "nodeId": node_id,
                "type": agent.__class__.__name__,
                "state": state,
                "color": STATE_COLORS.get(state, "#94a3b8"),
                "connections": neighbor_ids,
            }
        )

    return nodes


def _node_to_agent_id(stock_model: StockMarketModel) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for node_id, agents in stock_model.agents_by_node:
        if agents:
            mapping[node_id] = int(agents[0].unique_id)
    return mapping
