from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InsiderData:
    stake_increased: bool
    open_market_buy: bool


@dataclass
class FinancialStabilityData:
    debt_ratio: float | None
    operating_cash_flows_3y: list[float]
