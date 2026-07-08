from typing import Annotated, Any

from fastapi import Query
from pydantic import BeforeValidator


def _empty_str_to_none(value: Any) -> Any:
    if value == "":
        return None
    return value


ScreenerMarketParam = Annotated[
    str,
    Query(description="Market universe (KOSPI or KOSDAQ)"),
]

ScreenerMinProbParam = Annotated[
    float | None,
    BeforeValidator(_empty_str_to_none),
    Query(ge=0.0, le=1.0, description="Minimum posterior probability"),
]

ScreenerLimitParam = Annotated[
    int | None,
    BeforeValidator(_empty_str_to_none),
    Query(ge=1, le=200, description="Max number of tickers to screen"),
]
