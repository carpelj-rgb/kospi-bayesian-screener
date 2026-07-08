from datetime import date

from pydantic import BaseModel, Field


class ScreenerRow(BaseModel):
    ticker: str
    name: str
    market: str
    price: float | None = None
    pbr: float | None = None
    eps_revision_pct: float | None = None
    revision_score: float = Field(ge=0.0, le=1.0)
    flow_turnaround_score: float = Field(ge=0.0, le=1.0)
    vcp_score: float = Field(ge=0.0, le=1.0)
    roe_turnaround_score: float = Field(ge=0.0, le=1.0)
    insider_score: float = Field(ge=0.0, le=1.0)
    financial_stability_score: float = Field(ge=0.0, le=1.0)
    factor_tags: list[str] = Field(default_factory=list)
    posterior_up_prob: float = Field(ge=0.0, le=1.0)
    posterior_up_prob_pct: float = Field(ge=0.0, le=100.0)
    rank: int
    as_of: date


class ScreenerResponse(BaseModel):
    market: str
    as_of: date
    count: int
    rows: list[ScreenerRow]
    warnings: list[str] = Field(default_factory=list)


class FactorBreakdown(BaseModel):
    factor: str
    raw_value: float | None
    active: bool
    score: float
    weight: float | None = None
    likelihood_ratio: float
    logit_contribution: float


class StockDetailResponse(BaseModel):
    row: ScreenerRow
    prior_up_prob: float
    prior_odds: float
    posterior_odds: float
    breakdown: list[FactorBreakdown]
