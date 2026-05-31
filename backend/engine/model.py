"""Mesa model and market mechanics for the stock simulation engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import mesa
import networkx as nx
from mesa.space import NetworkGrid

from backend.engine.agent import (
    InstitutionalInvestor,
    InvestorState,
    Order,
    RetailInvestor,
)


@dataclass(frozen=True, slots=True)
class AgentChat:
    """Chat message produced by a panic retail investor in one tick."""

    agent_id: int
    message: str


@dataclass(frozen=True, slots=True)
class MarketEvent:
    """Market event emitted by stochastic shock and price-limit mechanics."""

    type: str
    message: str
    severity: str
    tick: int
    volume: int | None = None
    count: int | None = None


class StockMarketModel(mesa.Model):
    """Stock market simulation with social contagion and simple LOB pricing."""

    def __init__(
        self,
        num_retail: int = 100,
        num_institutional: int = 5,
        beta: float = 0.15,
        base_price: float = 100.0,
        price_impact: float = 0.02,
        upper_limit_percent: float = 0.25,
        lower_limit_percent: float = 0.15,
        initial_aware_fraction: float = 0.10,
        initial_panic_fraction: float = 0.05,
        network_degree: int = 4,
        retail_order_quantity: int = 1,
        institutional_order_quantity: int = 10,
        shock_enabled: bool = False,
        shock_probability: float = 0.0,
        shock_cooldown_ticks: int = 5,
        shock_min_volume: int = 25,
        shock_max_volume: int = 80,
        panic_drawdown_threshold: float = 0.05,
        panic_sensitivity: float = 8.0,
        panic_sell_multiplier: int = 3,
        chat_rotator: Any | None = None,
        chat_probability: float = 0.05,
        chat_mode: str = "scripted",
        rng: int | None = None,
    ) -> None:
        super().__init__(rng=rng)

        if num_retail < 0 or num_institutional < 0:
            raise ValueError("agent counts must be non-negative")
        if num_retail + num_institutional <= 0:
            raise ValueError("model requires at least one agent")
        if base_price <= 0:
            raise ValueError("base_price must be positive")

        self.num_retail = num_retail
        self.num_institutional = num_institutional
        self.beta = self._clamp(beta, 0.0, 1.0)
        self.base_price = float(base_price)
        self.current_price = float(base_price)
        self.price_impact = max(0.0, price_impact)
        self.upper_limit_percent = self._clamp(upper_limit_percent, 0.0, 1.0)
        self.lower_limit_percent = self._clamp(lower_limit_percent, 0.0, 1.0)
        self.upper_price_limit = self.base_price * (1 + self.upper_limit_percent)
        self.lower_price_limit = self.base_price * (1 - self.lower_limit_percent)
        self.upper_limit_triggered = False
        self.lower_limit_triggered = False
        self.last_order_imbalance = 0.0
        self.last_buy_volume = 0
        self.last_sell_volume = 0
        self._orders: list[Order] = []
        self.previous_price = float(base_price)
        self.last_price_drawdown = 0.0
        self.market_regime = "normal"
        self.last_shock_volume = 0
        self.latest_events: list[MarketEvent] = []
        self.shock_enabled = shock_enabled
        self.shock_probability = self._clamp(shock_probability, 0.0, 1.0)
        self.shock_cooldown_ticks = max(0, shock_cooldown_ticks)
        self.shock_min_volume = max(1, shock_min_volume)
        self.shock_max_volume = max(self.shock_min_volume, shock_max_volume)
        self.panic_drawdown_threshold = self._clamp(
            panic_drawdown_threshold,
            0.0,
            1.0,
        )
        self.panic_sensitivity = max(0.0, panic_sensitivity)
        self.panic_sell_multiplier = max(1, panic_sell_multiplier)
        self._shock_cooldown_remaining = 0
        self._panic_sell_active = False
        self.chat_rotator = chat_rotator
        self.chat_probability = self._clamp(chat_probability, 0.0, 1.0)
        self.chat_mode = chat_mode if chat_mode in {"scripted", "ai"} else "scripted"
        self.latest_chats: list[AgentChat] = []

        graph = self._build_network(
            total_agents=num_retail + num_institutional,
            network_degree=network_degree,
        )
        self.grid = NetworkGrid(graph)

        self._create_agents(
            initial_aware_fraction=self._clamp(initial_aware_fraction, 0.0, 1.0),
            initial_panic_fraction=self._clamp(initial_panic_fraction, 0.0, 1.0),
            retail_order_quantity=retail_order_quantity,
            institutional_order_quantity=institutional_order_quantity,
        )

    def step(self) -> None:
        """Run one simulation tick and update price from order imbalance."""
        self._orders = []
        self.latest_chats = []
        self.latest_events = []
        self.previous_price = self.current_price
        self.last_shock_volume = 0
        self._panic_sell_active = self.shock_enabled and self.market_regime in {
            "shock",
            "panic",
            "lower_limit",
        }
        shock_triggered = self._maybe_submit_market_maker_dump()
        if shock_triggered:
            self._panic_sell_active = True

        self.agents.shuffle_do("step")
        self._discover_price()
        self._update_drawdown()
        panic_count = self._apply_crash_panic()
        self._update_market_regime(
            shock_triggered=shock_triggered,
            panic_count=panic_count,
        )
        if self.chat_mode == "scripted":
            self.latest_chats.append(self.generate_scripted_chat())
        self._tick_shock_cooldown()

    def submit_order(self, order: Order) -> None:
        """Add an order intent to the current tick's aggregate order book."""
        if order.quantity <= 0:
            return
        self._orders.append(order)

    def should_panic_sell(self) -> bool:
        """Return whether panic retail should sell instead of FOMO-buy this tick."""
        return self._panic_sell_active

    def maybe_generate_chat(self, agent: RetailInvestor) -> None:
        """Generate panic chat for an agent with bounded per-tick probability."""
        if self.chat_mode != "ai":
            return
        if self.chat_rotator is None:
            return
        if self.random.random() >= self.chat_probability:
            return

        context = (
            f"price={self.current_price:.2f}, "
            f"imbalance={self.last_order_imbalance:.2f}, "
            f"state={agent.state}"
        )
        try:
            message = self.chat_rotator.generate_chat(context=context)
        except Exception:
            return

        if message:
            self.latest_chats.append(
                AgentChat(agent_id=int(agent.unique_id), message=message)
            )

    def generate_scripted_chat(self) -> AgentChat:
        if self.market_regime in {"shock", "panic", "lower_limit"} or self.last_shock_volume:
            messages = (
                "market dump, panik mulai kerasa",
                "mending cutloss dulu sebelum makin dalam",
                "seller brutal, jangan serok asal",
            )
        elif self.last_order_imbalance > 0.12 or self.current_price > self.previous_price:
            messages = (
                "to the moon, buyer masih kuat",
                "harga naik, FOMO mulai panas",
                "breakout nih, jangan ketinggalan",
            )
        else:
            messages = (
                "sideways dulu, tunggu breakout",
                "market masih sepi, sabar entry",
                "belum jelas arahnya, pantau volume",
            )
        return AgentChat(
            agent_id=0,
            message=self.random.choice(messages),
        )

    def _maybe_submit_market_maker_dump(self) -> bool:
        if not self.shock_enabled:
            return False
        if self._shock_cooldown_remaining > 0:
            return False
        if self.random.random() >= self.shock_probability:
            return False

        volume = self.random.randint(self.shock_min_volume, self.shock_max_volume)
        self.last_shock_volume = volume
        self._shock_cooldown_remaining = self.shock_cooldown_ticks
        self.submit_order(Order(agent_id=0, side="sell", quantity=volume))
        self.latest_events.append(
            MarketEvent(
                type="market_maker_dump",
                message=f"market maker dump sell volume {volume}",
                severity="danger",
                tick=self.steps,
                volume=volume,
            )
        )
        return True

    def _build_network(self, total_agents: int, network_degree: int) -> nx.Graph:
        if total_agents <= 1:
            return nx.empty_graph(total_agents)

        edge_count = min(max(1, network_degree // 2), total_agents - 1)
        seed = int(self.rng.integers(0, 2**32 - 1))
        return nx.barabasi_albert_graph(total_agents, edge_count, seed=seed)

    def _create_agents(
        self,
        initial_aware_fraction: float,
        initial_panic_fraction: float,
        retail_order_quantity: int,
        institutional_order_quantity: int,
    ) -> None:
        retail_states = self._initial_retail_states(
            initial_aware_fraction=initial_aware_fraction,
            initial_panic_fraction=initial_panic_fraction,
        )

        node_ids = list(self.grid.G.nodes)
        for index, state in enumerate(retail_states):
            agent = RetailInvestor(
                model=self,
                state=state,
                base_quantity=retail_order_quantity,
            )
            self.grid.place_agent(agent, node_ids[index])

        offset = len(retail_states)
        for index in range(self.num_institutional):
            agent = InstitutionalInvestor(
                model=self,
                base_quantity=institutional_order_quantity,
            )
            self.grid.place_agent(agent, node_ids[offset + index])

    def _initial_retail_states(
        self,
        initial_aware_fraction: float,
        initial_panic_fraction: float,
    ) -> list[InvestorState]:
        panic_count = self._fraction_count(self.num_retail, initial_panic_fraction)
        aware_count = self._fraction_count(self.num_retail, initial_aware_fraction)
        aware_count = min(aware_count, self.num_retail - panic_count)
        neutral_count = self.num_retail - panic_count - aware_count

        states: list[InvestorState] = (
            ["P"] * panic_count
            + ["A"] * aware_count
            + ["N"] * neutral_count
        )
        self.random.shuffle(states)
        return states

    def _discover_price(self) -> None:
        buy_volume = self._volume_for("buy")
        sell_volume = self._volume_for("sell")
        total_volume = buy_volume + sell_volume

        self.last_buy_volume = buy_volume
        self.last_sell_volume = sell_volume

        if total_volume == 0:
            self.last_order_imbalance = 0.0
            self.upper_limit_triggered = False
            self.lower_limit_triggered = False
            return

        imbalance = (buy_volume - sell_volume) / total_volume
        candidate_price = self.current_price * (1 + self.price_impact * imbalance)
        bounded_price = self._clamp(
            candidate_price,
            self.lower_price_limit,
            self.upper_price_limit,
        )

        self.last_order_imbalance = imbalance
        self.current_price = bounded_price
        self.upper_limit_triggered = bounded_price >= self.upper_price_limit
        self.lower_limit_triggered = bounded_price <= self.lower_price_limit

    def _update_drawdown(self) -> None:
        if self.previous_price <= 0:
            self.last_price_drawdown = 0.0
            return
        raw_drawdown = (self.previous_price - self.current_price) / self.previous_price
        self.last_price_drawdown = max(0.0, raw_drawdown)

    def _apply_crash_panic(self) -> int:
        panic_probability = self._panic_probability()
        if panic_probability <= 0:
            return 0

        panic_count = 0
        for agent in self.agents:
            if not isinstance(agent, RetailInvestor):
                continue
            if agent.state == "P":
                continue
            if self.random.random() < panic_probability:
                agent.state = "P"
                panic_count += 1

        if panic_count:
            self.latest_events.append(
                MarketEvent(
                    type="retail_panic",
                    message=f"{panic_count} retail investors entered panic",
                    severity="warning",
                    tick=self.steps,
                    count=panic_count,
                )
            )
        return panic_count

    def _panic_probability(self) -> float:
        if not self.shock_enabled:
            return 0.0
        if self.lower_limit_triggered:
            return 1.0

        panic_pressure = (
            max(0.0, self.last_price_drawdown - self.panic_drawdown_threshold)
            * self.panic_sensitivity
        )
        return self._clamp(panic_pressure, 0.0, 1.0)

    def _update_market_regime(self, shock_triggered: bool, panic_count: int) -> None:
        if self.lower_limit_triggered:
            self.market_regime = "lower_limit"
            self.latest_events.append(
                MarketEvent(
                    type="lower_limit_triggered",
                    message="price touched lower price limit",
                    severity="danger",
                    tick=self.steps,
                )
            )
        elif self.upper_limit_triggered:
            self.market_regime = "upper_limit"
            self.latest_events.append(
                MarketEvent(
                    type="upper_limit_triggered",
                    message="price touched upper price limit",
                    severity="success",
                    tick=self.steps,
                )
            )
        elif panic_count > 0 or self.last_price_drawdown >= self.panic_drawdown_threshold:
            self.market_regime = "panic"
        elif shock_triggered:
            self.market_regime = "shock"
        else:
            self.market_regime = "normal"

    def _tick_shock_cooldown(self) -> None:
        if self._shock_cooldown_remaining > 0:
            self._shock_cooldown_remaining -= 1

    def _volume_for(self, side: str) -> int:
        return sum(order.quantity for order in self._orders if order.side == side)

    @staticmethod
    def _fraction_count(total: int, fraction: float) -> int:
        if total <= 0 or fraction <= 0:
            return 0
        return max(1, int(total * fraction))

    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        return min(max(value, lower), upper)

    @property
    def orders(self) -> tuple[Order, ...]:
        """Read-only view of orders submitted during the latest tick."""
        return tuple(self._orders)

    @property
    def chats(self) -> tuple[AgentChat, ...]:
        """Read-only chat messages produced during the latest tick."""
        return tuple(self.latest_chats)

    @property
    def events(self) -> tuple[MarketEvent, ...]:
        """Read-only market events produced during the latest tick."""
        return tuple(self.latest_events)

    @property
    def agents_by_node(self) -> Iterable[tuple[int, list[mesa.Agent]]]:
        """Yield node IDs with their colocated agents for API/front-end mapping."""
        for node_id in self.grid.G.nodes:
            yield node_id, list(self.grid.G.nodes[node_id]["agent"])
