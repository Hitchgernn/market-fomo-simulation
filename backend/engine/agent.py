"""Agent definitions for the Mesa stock market simulation engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import mesa

if TYPE_CHECKING:
    from backend.engine.model import StockMarketModel


InvestorState = Literal["N", "A", "P"]
OrderSide = Literal["buy", "sell"]


@dataclass(frozen=True, slots=True)
class Order:
    """Simple order used by the aggregate limit order book."""

    agent_id: int
    side: OrderSide
    quantity: int


class RetailInvestor(mesa.Agent):
    """Retail investor with stochastic social exposure behavior."""

    def __init__(
        self,
        model: StockMarketModel,
        state: InvestorState = "N",
        base_quantity: int = 1,
    ) -> None:
        super().__init__(model)
        self.state: InvestorState = state
        self.base_quantity = max(1, base_quantity)

    def step(self) -> None:
        """Advance investor state and submit one market intent order."""
        if self.state == "N":
            panic_neighbors = self._count_panic_neighbors()
            exposure_probability = 1 - (1 - self.model.beta) ** panic_neighbors
            if self.model.random.random() < exposure_probability:
                self.state = "A"

        if self.state == "P":
            self.model.maybe_generate_chat(self)

        self.model.submit_order(self._build_order())

    def _count_panic_neighbors(self) -> int:
        if self.pos is None:
            return 0

        neighbors = self.model.grid.get_neighbors(self.pos)
        return sum(
            1
            for neighbor in neighbors
            if getattr(neighbor, "state", None) == "P"
        )

    def _build_order(self) -> Order:
        if self.state == "P":
            if self.model.should_panic_sell():
                side: OrderSide = "sell"
                quantity = self.base_quantity * self.model.panic_sell_multiplier
            else:
                side = "buy"
                quantity = self.base_quantity * 3
        elif self.state == "A":
            side = "buy"
            quantity = self.base_quantity * 2
        else:
            side = "sell" if self.model.random.random() < 0.45 else "buy"
            quantity = self.base_quantity

        return Order(
            agent_id=int(self.unique_id),
            side=side,
            quantity=quantity,
        )


class InstitutionalInvestor(mesa.Agent):
    """Institutional investor with larger stabilizing order flow."""

    def __init__(
        self,
        model: StockMarketModel,
        state: InvestorState = "A",
        base_quantity: int = 10,
    ) -> None:
        super().__init__(model)
        self.state: InvestorState = state
        self.base_quantity = max(1, base_quantity)

    def step(self) -> None:
        """Submit a larger order biased against extreme price deviation."""
        self.model.submit_order(self._build_order())

    def _build_order(self) -> Order:
        upper_anchor = self.model.base_price * 1.05
        lower_anchor = self.model.base_price * 0.95

        if self.model.current_price > upper_anchor:
            side: OrderSide = "sell"
        elif self.model.current_price < lower_anchor:
            side = "buy"
        else:
            side = "buy" if self.model.random.random() < 0.5 else "sell"

        return Order(
            agent_id=int(self.unique_id),
            side=side,
            quantity=self.base_quantity,
        )
