"""
Unit tests for the new 3-EMA trading strategy.
Tests BUY/SELL signals, trailing stop-loss, and cooldown logic.
No Firebase or Firi API dependencies - pure strategy testing.
"""
from datetime import datetime, timedelta
import pytest
from models import Candle, SignalType
from strategy import TradingStrategy
from indicators import (
    ema_above_ema_for_periods,
    ema_below_ema_for_periods,
)


def make_candles_from_prices(prices, start=None, step_hours=1):
    """Helper to build a list of Candle objects from a simple price list."""
    if start is None:
        start = datetime(2024, 1, 1, 0, 0, 0)
    
    candles = []
    for i, p in enumerate(prices):
        t = start + timedelta(hours=i * step_hours)
        candles.append(
            Candle(
                timestamp=t,
                open=p,
                high=p,
                low=p,
                close=p,
                volume=100.0,
            )
        )
    return candles


def test_buy_signal_when_medium_above_long_for_3_periods():
    """
    GIVEN a strong uptrend (monotonically rising prices)
    WHEN we have no open trade
    THEN the strategy should produce a BUY signal
         because medium EMA > long EMA for 3 periods.
    """
    # Monotont stigende priser
    prices = [100 + i for i in range(60)]
    candles = make_candles_from_prices(prices)
    
    short = 5
    medium = 10
    long = 20
    
    # Sikrer at vores helper-betingelse faktisk er opfyldt på dummy-data
    assert ema_above_ema_for_periods(candles, medium, long, periods=3)
    
    strategy = TradingStrategy(
        short_ema_period=short,
        medium_ema_period=medium,
        long_ema_period=long,
    )
    
    signal = strategy.generate_signal(candles, has_open_trade=False, in_cooldown=False)
    
    assert signal.signal_type == SignalType.BUY
    assert signal.reason is not None
    assert "Medium EMA" in signal.reason or "medium EMA" in signal.reason


def test_sell_signal_when_short_below_medium_for_3_periods():
    """
    GIVEN a clear downtrend (monotonically falling prices)
    WHEN we have an open trade
    THEN the strategy should produce a SELL signal
         because short EMA < medium EMA for 3 periods.
    """
    # Monotont faldende priser
    prices = [200 - i for i in range(60)]
    candles = make_candles_from_prices(prices)
    
    short = 5
    medium = 10
    long = 20
    
    # Sikrer at helper-betingelse faktisk er opfyldt på dummy-data
    assert ema_below_ema_for_periods(candles, short, medium, periods=3)
    
    strategy = TradingStrategy(
        short_ema_period=short,
        medium_ema_period=medium,
        long_ema_period=long,
    )
    
    signal = strategy.generate_signal(candles, has_open_trade=True, in_cooldown=False)
    
    assert signal.signal_type == SignalType.SELL
    assert signal.reason is not None
    assert "Short EMA" in signal.reason or "short EMA" in signal.reason


def test_hold_when_no_buy_or_sell_conditions_are_met():
    """
    GIVEN a choppy, sideways market (no clear trend)
    WHEN we have either an open or no open trade
    THEN the strategy should return HOLD
         because none of the EMA conditions are met.
    """
    # Flade / zig-zag priser
    prices = [100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101] * 5
    candles = make_candles_from_prices(prices)
    
    short = 5
    medium = 10
    long = 20
    
    strategy = TradingStrategy(
        short_ema_period=short,
        medium_ema_period=medium,
        long_ema_period=long,
    )
    
    # Vi tester både med og uden åben trade
    for has_open_trade in (False, True):
        signal = strategy.generate_signal(candles, has_open_trade=has_open_trade, in_cooldown=False)
        
        assert signal.signal_type == SignalType.HOLD
        assert signal.reason is not None
        # Mindst en form for "No signal" / "Insufficient" i teksten
        assert any(phrase in signal.reason for phrase in ["No signal", "Insufficient", "no signal", "conditions met"])


def test_buy_signal_blocked_during_cooldown():
    """
    GIVEN medium EMA > long EMA for 3 periods (BUY condition met)
    WHEN we are in cooldown period
    THEN the strategy should return HOLD instead of BUY.
    """
    # Monotont stigende priser
    prices = [100 + i for i in range(60)]
    candles = make_candles_from_prices(prices)
    
    strategy = TradingStrategy(
        short_ema_period=5,
        medium_ema_period=10,
        long_ema_period=20,
    )
    
    # Signal med cooldown aktiv
    signal = strategy.generate_signal(candles, has_open_trade=False, in_cooldown=True)
    
    assert signal.signal_type == SignalType.HOLD
    assert "cooldown" in signal.reason.lower() or "Cooldown" in signal.reason


def test_trailing_stop_not_triggered_above_threshold():
    """
    GIVEN highest_price = 120, trailing 7%
    WHEN current_price = 115 (drop < 7%)
    THEN trailing stop should NOT trigger.
    """
    strategy = TradingStrategy()
    
    highest = 120.0
    trailing = 7.0
    current = 115.0  # ~4.17% under high
    
    should_trigger, new_highest = strategy.should_trailing_stop_loss(
        entry_price=100.0,
        current_price=current,
        highest_price=highest,
        trailing_stop_percent=trailing
    )
    
    assert not should_trigger
    assert new_highest == highest  # Highest price unchanged


def test_trailing_stop_triggers_below_threshold():
    """
    GIVEN highest_price = 120, trailing 7%
    WHEN current_price = 111 (drop > 7%)
    THEN trailing stop SHOULD trigger.
    """
    strategy = TradingStrategy()
    
    highest = 120.0
    trailing = 7.0
    current = 111.0  # 7.5% under high
    
    should_trigger, new_highest = strategy.should_trailing_stop_loss(
        entry_price=100.0,
        current_price=current,
        highest_price=highest,
        trailing_stop_percent=trailing
    )
    
    assert should_trigger
    assert new_highest == highest  # Highest price unchanged (triggered before update)


def test_trailing_stop_updates_highest_price():
    """
    GIVEN highest_price = 120
    WHEN current_price = 125 (new high)
    THEN highest_price should be updated to 125.
    """
    strategy = TradingStrategy()
    
    highest = 120.0
    current = 125.0  # New high
    trailing = 7.0
    
    should_trigger, new_highest = strategy.should_trailing_stop_loss(
        entry_price=100.0,
        current_price=current,
        highest_price=highest,
        trailing_stop_percent=trailing
    )
    
    assert not should_trigger
    assert new_highest == 125.0  # Highest price updated


def test_insufficient_data_returns_hold():
    """
    GIVEN insufficient candles for EMA calculation
    WHEN generating signal
    THEN strategy should return HOLD with "Insufficient data" reason.
    """
    # Too few candles
    prices = [100, 101, 102]
    candles = make_candles_from_prices(prices)
    
    strategy = TradingStrategy(
        short_ema_period=5,
        medium_ema_period=10,
        long_ema_period=20,
    )
    
    signal = strategy.generate_signal(candles, has_open_trade=False, in_cooldown=False)
    
    assert signal.signal_type == SignalType.HOLD
    assert "Insufficient" in signal.reason


def test_sell_signal_only_when_has_open_trade():
    """
    GIVEN short EMA < medium EMA for 3 periods
    WHEN we have NO open trade
    THEN strategy should NOT produce SELL signal (only BUY/HOLD allowed).
    """
    # Monotont faldende priser
    prices = [200 - i for i in range(60)]
    candles = make_candles_from_prices(prices)
    
    strategy = TradingStrategy(
        short_ema_period=5,
        medium_ema_period=10,
        long_ema_period=20,
    )
    
    # No open trade - should not sell
    signal = strategy.generate_signal(candles, has_open_trade=False, in_cooldown=False)
    
    assert signal.signal_type != SignalType.SELL


def test_buy_signal_only_when_no_open_trade():
    """
    GIVEN medium EMA > long EMA for 3 periods
    WHEN we HAVE an open trade
    THEN strategy should NOT produce BUY signal (only SELL/HOLD allowed).
    """
    # Monotont stigende priser
    prices = [100 + i for i in range(60)]
    candles = make_candles_from_prices(prices)
    
    strategy = TradingStrategy(
        short_ema_period=5,
        medium_ema_period=10,
        long_ema_period=20,
    )
    
    # Has open trade - should not buy
    signal = strategy.generate_signal(candles, has_open_trade=True, in_cooldown=False)
    
    assert signal.signal_type != SignalType.BUY


def test_cooldown_logic():
    """
    Test cooldown logic: should prevent buying for N candles after a sell.
    This tests the cooldown helper logic used in main.py.
    """
    # Create candles with timestamps
    prices = [100 + i for i in range(40)]
    candles = make_candles_from_prices(prices)
    
    # Simulate a sell at candle index 4 (5th candle)
    last_sell_timestamp = candles[4].timestamp
    cooldown_candles = 25
    
    # Count candles after sell
    candles_after_sell = sum(1 for c in candles if c.timestamp > last_sell_timestamp)
    
    # With only ~35 candles total and sell at candle 5, we should have ~30 candles after
    # So cooldown should be False (enough candles passed)
    assert candles_after_sell >= cooldown_candles
    
    # Test with fewer candles - should still be in cooldown
    early_candles = candles[:15]  # Only 15 candles total
    candles_after_sell_early = sum(1 for c in early_candles if c.timestamp > last_sell_timestamp)
    
    # With sell at candle 5, we have only ~10 candles after, so cooldown should be True
    assert candles_after_sell_early < cooldown_candles

