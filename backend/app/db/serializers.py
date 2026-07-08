from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

import pandas as pd

from app.factors.models import TickerFactorInputs

if TYPE_CHECKING:
    from app.factors.pipeline import FactorFrame


def _series_to_dict(series: pd.Series) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for key, value in series.items():
        if pd.isna(value):
            out[str(key)] = None
        else:
            out[str(key)] = float(value)
    return out


def _dict_to_series(data: dict[str, float | None]) -> pd.Series:
    cleaned = {k: (float(v) if v is not None else float("nan")) for k, v in data.items()}
    return pd.Series(cleaned, dtype="float64")


def factor_frame_to_json(frame: FactorFrame) -> str:
    payload = {
        "tickers": frame.tickers,
        "as_of": frame.as_of.date().isoformat(),
        "prices": _series_to_dict(frame.prices),
        "pbr": _series_to_dict(frame.pbr),
        "eps_revision_pct": _series_to_dict(frame.eps_revision_pct),
        "revision_score": _series_to_dict(frame.revision_score),
        "flow_turnaround_score": _series_to_dict(frame.flow_turnaround_score),
        "vcp_score": _series_to_dict(frame.vcp_score),
        "roe_turnaround_score": _series_to_dict(frame.roe_turnaround_score),
        "insider_score": _series_to_dict(frame.insider_score),
        "financial_stability_score": _series_to_dict(frame.financial_stability_score),
        "factor_inputs": {
            ticker: asdict(inputs)
            for ticker, inputs in frame.factor_inputs.items()
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def factor_frame_from_json(raw: str) -> FactorFrame:
    from app.factors.pipeline import FactorFrame

    payload = json.loads(raw)
    tickers: list[str] = payload["tickers"]
    factor_inputs = {
        ticker: TickerFactorInputs(**values)
        for ticker, values in payload["factor_inputs"].items()
    }
    return FactorFrame(
        tickers=tickers,
        prices=_dict_to_series(payload.get("prices", {})),
        pbr=_dict_to_series(payload.get("pbr", {})),
        eps_revision_pct=_dict_to_series(payload.get("eps_revision_pct", {})),
        revision_score=_dict_to_series(payload.get("revision_score", {})),
        flow_turnaround_score=_dict_to_series(payload.get("flow_turnaround_score", {})),
        vcp_score=_dict_to_series(payload.get("vcp_score", {})),
        roe_turnaround_score=_dict_to_series(payload.get("roe_turnaround_score", {})),
        insider_score=_dict_to_series(payload.get("insider_score", {})),
        financial_stability_score=_dict_to_series(payload.get("financial_stability_score", {})),
        factor_inputs=factor_inputs,
        as_of=pd.Timestamp(payload["as_of"]),
    )


def tickers_key(tickers: list[str]) -> str:
    return ",".join(sorted(tickers))


def today_iso(reference: date | None = None) -> str:
    return (reference or date.today()).isoformat()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
