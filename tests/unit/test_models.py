"""Unit tests for data models."""
from datetime import datetime

from models import Trade, TradeStatus


def test_trade_to_dict_includes_history_fields():
    t = Trade(
        trade_id="a1",
        pair="ETH/DKK",
        side="buy",
        price=100.0,
        quantity=0.5,
        status=TradeStatus.CLOSED,
        timestamp=datetime(2025, 6, 1, 10, 0, 0),
        close_price=110.0,
        close_timestamp=datetime(2025, 6, 2, 10, 0, 0),
        profit_loss=5.0,
        profit_loss_percent=10.0,
        quote_spent=200.0,
        quote_proceeds=205.0,
    )
    d = t.to_dict()
    assert d["pair"] == "ETH/DKK"
    assert d["buy_amount_base"] == 0.5
    assert d["quote_currency"] == "DKK"
    assert d["quote_spent"] == 200.0
    assert d["quote_proceeds"] == 205.0
    assert d["profit_quote"] == 5.0
    assert d["profit_loss"] == 5.0


def test_trade_from_dict_roundtrip_and_profit_quote_fallback():
    t = Trade(
        trade_id="a1",
        pair="ETH/DKK",
        side="buy",
        price=100.0,
        quantity=0.5,
        status=TradeStatus.OPEN,
        timestamp=datetime(2025, 6, 1, 10, 0, 0),
    )
    d = t.to_dict()
    d.pop("profit_loss", None)
    d["profit_quote"] = 3.0
    restored = Trade.from_dict(d)
    assert restored.profit_loss == 3.0

