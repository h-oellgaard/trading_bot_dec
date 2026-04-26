"""
Unit tests for main.py TradingBot.
Uses mocks to avoid Firebase/Firi API dependencies.
"""
import logging
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from models import Signal, SignalType, Trade, TradeStatus
from trader import round_quantity


def _mock_firebase_handler():
    """Return a mock Firebase handler that won't break logging."""
    h = MagicMock()
    h.level = logging.WARNING
    return h


def test_poll_interval_from_trading_config():
    """
    GIVEN trading_config defines POLL_INTERVAL
    WHEN TradingBot is initialized
    THEN bot.poll_interval matches trading_config.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)
    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", MagicMock()):
            with patch("main.FirebaseStore", MagicMock()):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    from main import TradingBot
                    from settings.trading_config import POLL_INTERVAL

                    bot = TradingBot()
                    assert bot.poll_interval == POLL_INTERVAL


def test_firi_format_applied_at_startup():
    """
    GIVEN Firi orderbook returns price/amount format
    WHEN TradingBot is initialized
    THEN trader uses Firi's price_decimals and quantity_decimals.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)
    mock_trader = MagicMock()

    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
            with patch("main.FiriTrader", return_value=mock_trader):
                with patch("main.FirebaseStore", MagicMock()):
                    with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                        from main import TradingBot

                        bot = TradingBot()
                        from settings.trading_config import TRADING_PAIR
                        mock_data_fetcher.get_order_format.assert_called_once_with(TRADING_PAIR)
                        assert mock_trader.price_decimals == 2
                        assert mock_trader.quantity_decimals == 8


def test_firi_format_uses_trading_pair_from_trading_config():
    """
    GIVEN trading_config defines TRADING_PAIR
    WHEN TradingBot is initialized
    THEN get_order_format is called with that pair.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)
    mock_trader = MagicMock()

    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", return_value=mock_trader):
            with patch("main.FirebaseStore", MagicMock()):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    from main import TradingBot

                    bot = TradingBot()
                    from settings.trading_config import TRADING_PAIR
                    mock_data_fetcher.get_order_format.assert_called_once_with(TRADING_PAIR)


def test_ema_periods_from_trading_config():
    """
    GIVEN trading_config defines SHORT/MEDIUM/LONG_EMA_PERIOD
    WHEN TradingBot is initialized
    THEN strategy uses those EMA periods.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)

    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", MagicMock()):
            with patch("main.FirebaseStore", MagicMock()):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    from main import TradingBot
                    from settings.trading_config import (
                        SHORT_EMA_PERIOD,
                        MEDIUM_EMA_PERIOD,
                        LONG_EMA_PERIOD,
                    )

                    bot = TradingBot()
                    assert bot.strategy.short_ema_period == SHORT_EMA_PERIOD
                    assert bot.strategy.medium_ema_period == MEDIUM_EMA_PERIOD
                    assert bot.strategy.long_ema_period == LONG_EMA_PERIOD


def test_execute_buy_signal_uses_fixed_quote_amount_and_fee():
    """
    GIVEN BUY_QUOTE_AMOUNT=200, FIRI_FEE_PERCENT=0.7, and sufficient DKK balance
    WHEN execute_buy_signal runs at a known price
    THEN quantity matches test_trade formula: (200/1.007)/price.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)
    mock_trader = MagicMock()
    mock_trader.get_balance.return_value = 500.0
    mock_firebase = MagicMock()
    mock_trader.place_buy_order.return_value = Trade(
        trade_id="1",
        pair="ETH/DKK",
        side="buy",
        price=10000.0,
        quantity=0.01,
        status=TradeStatus.OPEN,
        timestamp=datetime.now(),
    )

    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", return_value=mock_trader):
            with patch("main.FirebaseStore", return_value=mock_firebase):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    with patch("main.BUY_QUOTE_AMOUNT", 200.0):
                        with patch("main.FIRI_FEE_PERCENT", 0.7):
                            from main import TradingBot

                            bot = TradingBot()
                            signal = Signal(
                                signal_id="s1",
                                signal_type=SignalType.BUY,
                                timestamp=datetime.now(),
                                price=10000.0,
                                reason="test",
                            )
                            bot.execute_buy_signal(signal, current_price=10000.0)

    expected_qty = round_quantity((200.0 / 1.007) / 10000.0, decimals=8)
    saved = mock_firebase.save_trade.call_args[0][0]
    assert saved.quote_spent == 200.0
    mock_trader.place_buy_order.assert_called_once()
    call = mock_trader.place_buy_order.call_args
    assert call.kwargs["pair"] == bot.pair
    assert call.kwargs["price"] == 10000.0
    assert call.kwargs["quantity"] == expected_qty


def test_close_trade_save_trade_failure_when_price_unavailable():
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)
    mock_data_fetcher.get_current_price.return_value = None
    mock_trader = MagicMock()
    mock_firebase = MagicMock()
    open_trade = Trade(
        trade_id="buy-1",
        pair="ETH/DKK",
        side="buy",
        price=10_000.0,
        quantity=0.01,
        status=TradeStatus.OPEN,
        timestamp=datetime.now(),
    )
    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", return_value=mock_trader):
            with patch("main.FirebaseStore", return_value=mock_firebase):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    from main import TradingBot

                    bot = TradingBot()
                    bot.close_trade(open_trade, "signal")

    mock_firebase.save_trade_failure.assert_called_once()
    call = mock_firebase.save_trade_failure.call_args
    assert call.kwargs["operation"] == "sell"
    assert call.kwargs["pair"] == "ETH/DKK"
    assert "current price" in call.kwargs["error_message"].lower()
    mock_trader.place_sell_order.assert_not_called()


def test_close_trade_save_trade_failure_on_exception():
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)
    mock_data_fetcher.get_current_price.return_value = 11_000.0
    mock_trader = MagicMock()
    mock_trader.place_sell_order.side_effect = RuntimeError("Firi rejected")
    mock_firebase = MagicMock()
    open_trade = Trade(
        trade_id="buy-1",
        pair="ETH/DKK",
        side="buy",
        price=10_000.0,
        quantity=0.01,
        status=TradeStatus.OPEN,
        timestamp=datetime.now(),
    )
    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", return_value=mock_trader):
            with patch("main.FirebaseStore", return_value=mock_firebase):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    from main import TradingBot

                    bot = TradingBot()
                    bot.close_trade(open_trade, "test")

    mock_firebase.save_trade_failure.assert_called_once()
    kw = mock_firebase.save_trade_failure.call_args.kwargs
    assert kw["operation"] == "sell"
    assert "Firi rejected" in kw["error_message"]
    assert kw.get("exc_info")


def test_execute_buy_save_trade_failure_on_exception():
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)
    mock_trader = MagicMock()
    mock_trader.get_balance.return_value = 500.0
    mock_trader.place_buy_order.side_effect = RuntimeError("API down")
    mock_firebase = MagicMock()
    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", return_value=mock_trader):
            with patch("main.FirebaseStore", return_value=mock_firebase):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    with patch("main.BUY_QUOTE_AMOUNT", 200.0):
                        with patch("main.FIRI_FEE_PERCENT", 0.7):
                            from main import TradingBot

                            bot = TradingBot()
                            signal = Signal(
                                signal_id="s1",
                                signal_type=SignalType.BUY,
                                timestamp=datetime.now(),
                                price=10_000.0,
                                reason="golden cross",
                            )
                            bot.execute_buy_signal(signal, current_price=10_000.0)

    mock_firebase.save_trade_failure.assert_called_once()
    kw = mock_firebase.save_trade_failure.call_args.kwargs
    assert kw["operation"] == "buy"
    assert "API down" in kw["error_message"]
    assert kw["details"].get("signal_reason") == "golden cross"


def test_close_trade_profit_uses_quote_spent_and_appends_history():
    """
    GIVEN an open trade with quote_spent (DKK outlay) and a higher sell price
    WHEN close_trade runs
    THEN profit_quote = quote_proceeds - quote_spent and historical row is written.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)
    mock_data_fetcher.get_current_price.return_value = 11_000.0
    mock_trader = MagicMock()
    mock_trader.place_sell_order.return_value = Trade(
        trade_id="sell-1",
        pair="ETH/DKK",
        side="sell",
        price=11_000.0,
        quantity=0.01,
        status=TradeStatus.OPEN,
        timestamp=datetime.now(),
    )
    mock_firebase = MagicMock()
    open_trade = Trade(
        trade_id="buy-1",
        pair="ETH/DKK",
        side="buy",
        price=10_000.0,
        quantity=0.01,
        status=TradeStatus.OPEN,
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        quote_spent=200.0,
    )

    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", return_value=mock_trader):
            with patch("main.FirebaseStore", return_value=mock_firebase):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    from main import TradingBot

                    bot = TradingBot()
                    bot.close_trade(open_trade, "test")

    mock_firebase.save_trade.assert_called_once()
    saved = mock_firebase.save_trade.call_args[0][0]
    assert saved.status == TradeStatus.CLOSED
    assert saved.quote_proceeds == pytest.approx(110.0)
    assert saved.profit_loss == pytest.approx(110.0 - 200.0)
    mock_firebase.append_historical_trade.assert_called_once()
    hist_arg = mock_firebase.append_historical_trade.call_args[0][0]
    assert hist_arg.trade_id == "buy-1"
    assert hist_arg.profit_loss == saved.profit_loss


def test_invalid_trading_pair_raises_error():
    """
    GIVEN TRADING_PAIR is BZZ/DKK (pair that doesn't exist on Firi)
    WHEN TradingBot initializes and get_order_format returns None (Firi 404)
    THEN bot raises an error to the user, no silent fallback to defaults.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = None  # Firi 404 for non-existent pair

    with patch("main.TRADING_PAIR", "BZZ/DKK"):
        with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
            with patch("main.FiriTrader", MagicMock()):
                with patch("main.FirebaseStore", MagicMock()):
                    with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                        from main import TradingBot

                        with pytest.raises(ValueError, match="order format|BZZ/DKK|invalid pair"):
                            TradingBot()


def test_strategy_uses_ema_in_signals():
    """
    GIVEN strategy generates a BUY (medium/long golden cross fixture)
    WHEN we inspect the signal
    THEN it contains EMA values (short_ema, medium_ema, long_ema) and reason mentions EMA.
    """
    from strategy import TradingStrategy
    from tests.unit.test_new_strategy import make_candles_medium_long_golden_cross

    candles = make_candles_medium_long_golden_cross(10, 20, count=60)
    strategy = TradingStrategy(short_ema_period=5, medium_ema_period=10, long_ema_period=20)
    signal = strategy.generate_signal(candles, has_open_trade=False, in_cooldown=False)

    assert signal.signal_type == SignalType.BUY
    assert signal.short_ema is not None
    assert signal.medium_ema is not None
    assert signal.long_ema is not None
    assert "EMA" in signal.reason or "ema" in signal.reason
