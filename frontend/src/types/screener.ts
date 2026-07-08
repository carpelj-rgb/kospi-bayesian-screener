export interface ScreenerRow {
  ticker: string;
  name: string;
  market: string;
  price: number | null;
  pbr: number | null;
  eps_revision_pct: number | null;
  revision_score: number;
  flow_turnaround_score: number;
  vcp_score: number;
  roe_turnaround_score: number;
  insider_score: number;
  financial_stability_score: number;
  factor_tags: string[];
  posterior_up_prob: number;
  posterior_up_prob_pct: number;
  rank: number;
  as_of: string;
}

export interface ScreenerResponse {
  market: string;
  as_of: string;
  count: number;
  rows: ScreenerRow[];
  warnings?: string[];
}

export interface FactorBreakdown {
  factor: string;
  raw_value: number | null;
  active: boolean;
  score: number;
  weight: number | null;
  likelihood_ratio: number;
  logit_contribution: number;
}

export interface StockDetailResponse {
  row: ScreenerRow;
  prior_up_prob: number;
  prior_odds: number;
  posterior_odds: number;
  breakdown: FactorBreakdown[];
}
