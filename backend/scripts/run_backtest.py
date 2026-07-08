#!/usr/bin/env python3
"""
CLI / Jupyter helper for running backtests against SQLite factor snapshots.

Usage:
  cd backend && PYTHONPATH=. python scripts/run_backtest.py --market KOSPI --top-n 10
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.backtest_service import BacktestService  # noqa: E402


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Bayesian factor backtest from SQLite snapshots")
    parser.add_argument("--market", default="KOSPI")
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--start-date", dest="start_date", default=None)
    parser.add_argument("--end-date", dest="end_date", default=None)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    service = BacktestService()
    result = service.get_backtest(
        market=args.market,
        top_n=args.top_n,
        start_date=_parse_date(args.start_date),
        end_date=_parse_date(args.end_date),
    )
    payload = result.model_dump(mode="json")
    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
