from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TickerFactorInputs:
    pbr: float | None
    universe_pbr: list[float]
    net_revision_ratio: float | None
    earnings_surprise_pct: float | None
    inst_net_daily: list[float]
    combined_net_daily: list[float]
    trading_values: list[float]
    closes: list[float]
    opens: list[float]
    volumes: list[float]
    current_roe: float | None
    previous_roe: float | None
    insider_stake_increased: bool = False
    insider_open_market_buy: bool = False
    debt_ratio: float | None = None
    universe_debt_ratios: list[float] | None = None
    operating_cash_flows_3y: list[float] | None = None

    def __post_init__(self) -> None:
        if self.universe_debt_ratios is None:
            self.universe_debt_ratios = []
        if self.operating_cash_flows_3y is None:
            self.operating_cash_flows_3y = []
