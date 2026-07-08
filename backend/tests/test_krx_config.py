from app.data.providers.krx_config import configure_pykrx, get_stock_module, should_use_pykrx


def test_should_use_pykrx_enabled_by_default(monkeypatch):
    monkeypatch.delenv("PYKRX_ENABLED", raising=False)
    assert should_use_pykrx() is True


def test_should_use_pykrx_can_be_disabled(monkeypatch):
    monkeypatch.setenv("PYKRX_ENABLED", "false")
    assert should_use_pykrx() is False


def test_get_stock_module_suppresses_login_message(monkeypatch, capsys):
    monkeypatch.delenv("KRX_ID", raising=False)
    monkeypatch.delenv("KRX_PW", raising=False)

    import app.data.providers.krx_config as krx_config

    krx_config._configured = False
    krx_config._stock_module = None

    configure_pykrx()
    stock = get_stock_module()

    assert stock is not None
    captured = capsys.readouterr()
    assert "KRX_ID" not in captured.out
    assert "로그인" not in captured.out
