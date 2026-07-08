export interface BacktestMetrics {
  total_return: number;
  benchmark_total_return: number;
  max_drawdown: number;
  sharpe_ratio: number | null;
  periods: number;
  win_rate: number;
}

export interface BacktestEquityPoint {
  date: string;
  portfolio: number;
  benchmark: number;
}

export interface BacktestPeriodRow {
  rebalance_date: string;
  next_date: string;
  holdings: string[];
  period_return: number;
  benchmark_return: number;
}

export interface BacktestResponse {
  market: string;
  top_n: number;
  start_date: string | null;
  end_date: string | null;
  snapshot_dates_used: string[];
  metrics: BacktestMetrics;
  equity_curve: BacktestEquityPoint[];
  periods: BacktestPeriodRow[];
  warnings: string[];
}

export interface BacktestQueryParams {
  market?: string;
  top_n?: number;
  start_date?: string;
  end_date?: string;
}
