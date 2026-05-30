"""FastAPI entry point for the FOMO market simulation backend."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.engine.model import StockMarketModel
from backend.llm.rotator import AgentChatRotator


STATE_COLORS = {
    "N": "#22c55e",
    "A": "#eab308",
    "P": "#ef4444",
}


class SimulationConfig(BaseModel):
    """Runtime simulation parameters accepted from the frontend."""

    model_config = ConfigDict(populate_by_name=True)

    num_retail: int = Field(100, alias="numRetail", ge=0, le=1000)
    num_institutional: int = Field(5, alias="numInstitutional", ge=0, le=100)
    base_price: float = Field(100.0, alias="basePrice", gt=0)
    beta: float = Field(0.15, ge=0, le=1)
    price_impact: float = Field(0.02, alias="priceImpact", ge=0, le=1)
    initial_aware_fraction: float = Field(
        0.10,
        alias="initialAwareFraction",
        ge=0,
        le=1,
    )
    initial_panic_fraction: float = Field(
        0.05,
        alias="initialPanicFraction",
        ge=0,
        le=1,
    )
    upper_limit_percent: float = Field(0.25, alias="upperLimitPercent", ge=0, le=1)
    lower_limit_percent: float = Field(0.15, alias="lowerLimitPercent", ge=0, le=1)
    shock_enabled: bool = Field(False, alias="shockEnabled")
    shock_probability: float = Field(0.0, alias="shockProbability", ge=0, le=1)
    shock_cooldown_ticks: int = Field(5, alias="shockCooldownTicks", ge=0, le=1000)
    shock_min_volume: int = Field(25, alias="shockMinVolume", ge=1, le=1_000_000)
    shock_max_volume: int = Field(80, alias="shockMaxVolume", ge=1, le=1_000_000)
    panic_drawdown_threshold: float = Field(
        0.05,
        alias="panicDrawdownThreshold",
        ge=0,
        le=1,
    )
    panic_sensitivity: float = Field(8.0, alias="panicSensitivity", ge=0, le=1000)
    panic_sell_multiplier: int = Field(3, alias="panicSellMultiplier", ge=1, le=1000)
    rng: int | None = Field(None, ge=0)

    @model_validator(mode="after")
    def validate_agent_mix(self) -> "SimulationConfig":
        if self.num_retail + self.num_institutional <= 0:
            raise ValueError("simulation requires at least one agent")
        if self.initial_aware_fraction + self.initial_panic_fraction > 1:
            raise ValueError("aware and panic fractions cannot exceed 1 total")
        if self.shock_min_volume > self.shock_max_volume:
            raise ValueError("shockMinVolume cannot exceed shockMaxVolume")
        return self


def _read_api_keys() -> list[str]:
    raw_keys = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or ""
    return [key.strip() for key in raw_keys.split(",") if key.strip()]


def _build_chat_rotator() -> AgentChatRotator | None:
    api_keys = _read_api_keys()
    if not api_keys:
        return None
    return AgentChatRotator(api_keys=api_keys)


def create_model(config: SimulationConfig | None = None) -> StockMarketModel:
    """Create the long-lived simulation model used by the API process."""
    active_config = config or SimulationConfig()
    return StockMarketModel(
        num_retail=active_config.num_retail,
        num_institutional=active_config.num_institutional,
        beta=active_config.beta,
        base_price=active_config.base_price,
        price_impact=active_config.price_impact,
        upper_limit_percent=active_config.upper_limit_percent,
        lower_limit_percent=active_config.lower_limit_percent,
        initial_aware_fraction=active_config.initial_aware_fraction,
        initial_panic_fraction=active_config.initial_panic_fraction,
        shock_enabled=active_config.shock_enabled,
        shock_probability=active_config.shock_probability,
        shock_cooldown_ticks=active_config.shock_cooldown_ticks,
        shock_min_volume=active_config.shock_min_volume,
        shock_max_volume=active_config.shock_max_volume,
        panic_drawdown_threshold=active_config.panic_drawdown_threshold,
        panic_sensitivity=active_config.panic_sensitivity,
        panic_sell_multiplier=active_config.panic_sell_multiplier,
        chat_rotator=_build_chat_rotator(),
        rng=active_config.rng,
    )


current_config = SimulationConfig()
model = create_model(current_config)
app = FastAPI(title="FOMO Market Simulation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/state")
def state() -> dict[str, Any]:
    """Return the current simulation state without advancing a tick."""
    return _serialize_state(model)


@app.get("/tick")
def tick() -> dict[str, Any]:
    """Advance the simulation by one tick and return frontend-ready JSON."""
    model.step()
    return _serialize_state(model)


@app.post("/reset")
def reset(config: SimulationConfig) -> dict[str, Any]:
    """Reset the simulation with frontend-provided runtime parameters."""
    global current_config, model

    current_config = config
    model = create_model(config)
    return _serialize_state(model)


def _serialize_state(stock_model: StockMarketModel) -> dict[str, Any]:
    return {
        "tick": stock_model.steps,
        "config": current_config.model_dump(by_alias=True),
        "price": {
            "current": stock_model.current_price,
            "previous": stock_model.previous_price,
            "base": stock_model.base_price,
            "drawdown": stock_model.last_price_drawdown,
            "upperLimit": stock_model.upper_price_limit,
            "lowerLimit": stock_model.lower_price_limit,
            "upperLimitPercent": stock_model.upper_limit_percent,
            "lowerLimitPercent": stock_model.lower_limit_percent,
            "upperLimitTriggered": stock_model.upper_limit_triggered,
            "lowerLimitTriggered": stock_model.lower_limit_triggered,
        },
        "orderBook": {
            "buyVolume": stock_model.last_buy_volume,
            "sellVolume": stock_model.last_sell_volume,
            "imbalance": stock_model.last_order_imbalance,
        },
        "market": {
            "regime": stock_model.market_regime,
            "shockVolume": stock_model.last_shock_volume,
        },
        "events": [
            {
                "type": event.type,
                "message": event.message,
                "severity": event.severity,
                "tick": event.tick,
                "volume": event.volume,
                "count": event.count,
            }
            for event in stock_model.events
        ],
        "stateCounts": _state_counts(stock_model),
        "nodes": _serialize_nodes(stock_model),
        "chats": [
            {
                "agentId": chat.agent_id,
                "message": chat.message,
            }
            for chat in stock_model.chats
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


def _state_counts(stock_model: StockMarketModel) -> dict[str, int]:
    counts = {"N": 0, "A": 0, "P": 0}
    for _, agents in stock_model.agents_by_node:
        for agent in agents:
            state = getattr(agent, "state", "N")
            if state in counts:
                counts[state] += 1
    return counts
