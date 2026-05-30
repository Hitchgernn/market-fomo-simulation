"""Mesa model and market mechanics for the stock simulation engine."""

from __future__ import annotations

from typing import Iterable

import mesa
import networkx as nx
from mesa.space import NetworkGrid

from backend.engine.agent import (
    InstitutionalInvestor,
    InvestorState,
    Order,
    RetailInvestor,
)


class StockMarketModel(mesa.Model):
    """Stock market simulation with social contagion and simple LOB pricing."""

    def __init__(
        self,
        num_retail: int = 100,
        num_institutional: int = 5,
        beta: float = 0.15,
        base_price: float = 100.0,
        price_impact: float = 0.02,
        initial_aware_fraction: float = 0.10,
        initial_panic_fraction: float = 0.05,
        network_degree: int = 4,
        retail_order_quantity: int = 1,
        institutional_order_quantity: int = 10,
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
        self.ara_limit = self.base_price * 1.25
        self.arb_limit = self.base_price * 0.85
        self.ara_triggered = False
        self.arb_triggered = False
        self.last_order_imbalance = 0.0
        self.last_buy_volume = 0
        self.last_sell_volume = 0
        self._orders: list[Order] = []

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
        self.agents.shuffle_do("step")
        self._discover_price()

    def submit_order(self, order: Order) -> None:
        """Add an order intent to the current tick's aggregate order book."""
        if order.quantity <= 0:
            return
        self._orders.append(order)

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
            self.ara_triggered = False
            self.arb_triggered = False
            return

        imbalance = (buy_volume - sell_volume) / total_volume
        candidate_price = self.current_price * (1 + self.price_impact * imbalance)
        bounded_price = self._clamp(candidate_price, self.arb_limit, self.ara_limit)

        self.last_order_imbalance = imbalance
        self.current_price = bounded_price
        self.ara_triggered = bounded_price >= self.ara_limit
        self.arb_triggered = bounded_price <= self.arb_limit

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
    def agents_by_node(self) -> Iterable[tuple[int, list[mesa.Agent]]]:
        """Yield node IDs with their colocated agents for API/front-end mapping."""
        for node_id in self.grid.G.nodes:
            yield node_id, list(self.grid.G.nodes[node_id]["agent"])
