from datetime import date
from unittest.mock import MagicMock

from app.api.query_params import _empty_str_to_none
from app.api.v1.screener import list_screener
from app.schemas.screener import ScreenerResponse


def test_empty_str_to_none_coercion():
    assert _empty_str_to_none("") is None
    assert _empty_str_to_none(None) is None
    assert _empty_str_to_none("20") == "20"


def test_list_screener_passes_sanitized_optional_params():
    service = MagicMock()
    service.get_screener.return_value = ScreenerResponse(
        market="KOSPI",
        as_of=date.today(),
        count=0,
        rows=[],
    )

    list_screener(market="KOSPI", min_prob=None, limit=20, service=service)

    service.get_screener.assert_called_once_with(market="KOSPI", min_prob=None, limit=20)
