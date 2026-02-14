# Test Cases Review & Additional Test Recommendations

## Current Coverage Summary

| Module | File | Tests | Coverage |
|--------|------|-------|----------|
| **indicators** | test_indicators.py, test_indicator_correctness.py | 19 | Good – SMA, EMA, crossovers, period checks |
| **strategy** | test_new_strategy.py | 11 | Good – BUY/SELL/HOLD, cooldown, trailing stop |
| **models** | — | 0 | None |
| **data_fetcher** | — | 0 | None |
| **firebase_store** | — | 0 | Integration only |
| **trader** | — | 0 | Integration only |
| **main** | — | 0 | Integration only |

---

## Recommended Additional Test Cases

### 1. Indicators – Edge Cases & Negatives

| # | Test Case | Purpose |
|---|-----------|---------|
| 1.1 | `sma_crossover_returns_false_when_no_crossover` | Short SMA stays above long – no crossover, assert False |
| 1.2 | `ema_crossover_returns_false_when_no_crossover` | Short EMA stays above long – no crossover, assert False |
| 1.3 | `get_latest_sma_returns_none_when_insufficient_data` | Fewer candles than period → None |
| 1.4 | `get_latest_ema_returns_none_when_insufficient_data` | Fewer candles than period → None |
| 1.5 | `ema_below_sma_for_periods_true_with_downtrend` | Explicit True case with declining prices |
| 1.6 | `sma_with_empty_candles` | Empty list → all None or empty list |
| 1.7 | `ema_with_single_candle` | Single candle, period > 1 → all None |
| 1.8 | `ema_crossover_insufficient_candles_returns_false` | len(candles) < long_period + 1 → False |

---

### 2. Models – Serialization Round-Trip

| # | Test Case | Purpose |
|---|-----------|---------|
| 2.1 | `candle_to_dict_from_dict_roundtrip` | Candle → dict → Candle preserves data |
| 2.2 | `trade_to_dict_from_dict_roundtrip` | Trade → dict → Trade preserves data |
| 2.3 | `signal_to_dict_from_dict_roundtrip` | Signal → dict → Signal preserves data |
| 2.4 | `portfolio_state_to_dict_from_dict_roundtrip` | PortfolioState → dict → PortfolioState preserves data |
| 2.5 | `trade_with_optional_fields_roundtrip` | Trade with close_price, profit_loss, highest_price, etc. |
| 2.6 | `candle_from_dict_handles_missing_volume` | volume defaults to 0.0 when missing |

---

### 3. Strategy – Edge Cases & Signal Content

| # | Test Case | Purpose |
|---|-----------|---------|
| 3.1 | `signal_contains_ema_values_on_buy` | BUY signal has short_ema, medium_ema, long_ema populated |
| 3.2 | `signal_contains_ema_values_on_sell` | SELL signal has all EMA values |
| 3.3 | `trailing_stop_exact_boundary_7_percent` | current = highest * 0.93 → should trigger |
| 3.4 | `trailing_stop_just_above_boundary` | current = highest * 0.931 → should NOT trigger |
| 3.5 | `generate_signal_empty_candles` | Empty candles list → HOLD with safe handling |
| 3.6 | `generate_signal_single_candle` | Single candle → HOLD, no crash |
| 3.7 | `signal_has_valid_uuid` | signal_id is valid UUID format |
| 3.8 | `signal_timestamp_is_recent` | timestamp is within last few seconds |

---

### 4. Data Fetcher – Unit Tests (Mock HTTP)

| # | Test Case | Purpose |
|---|-----------|---------|
| 4.1 | `convert_trade_history_to_ohlc_single_candle` | Single trade → single Candle with correct OHLC |
| 4.2 | `convert_trade_history_to_ohlc_multiple_trades` | Multiple trades in same interval → correct OHLC |
| 4.3 | `convert_trade_history_to_ohlc_interval_30m` | Trades grouped by 30m interval |
| 4.4 | `convert_trade_history_handles_unix_timestamp` | Timestamp as int (seconds) parsed correctly |
| 4.5 | `convert_trade_history_handles_unix_timestamp_ms` | Timestamp as int (milliseconds) parsed correctly |
| 4.6 | `convert_trade_history_handles_iso_string` | Timestamp as ISO string parsed correctly |
| 4.7 | `convert_trade_history_empty_list` | Empty trades → empty list |
| 4.8 | `convert_trade_history_skips_invalid_trades` | Trades missing price/timestamp skipped |

---

### 5. Integration Tests (Optional – Require Mocks)

| # | Test Case | Purpose |
|---|-----------|---------|
| 5.1 | `trading_bot_run_iteration_insufficient_candles` | Mock fetcher returns empty → no crash, graceful return |
| 5.2 | `save_price_snapshot_creates_valid_candle` | Mock firebase → verify Candle structure saved |
| 5.3 | `execute_buy_signal_calculates_quantity` | Mock trader, balance 1000 → quantity = 0.95 * 1000 / price |

---

## Priority Order

1. **High** – Models (2.x): Simple, no mocks, prevents serialization bugs.
2. **High** – Indicators edge cases (1.1–1.8): Strengthens core logic.
3. **Medium** – Strategy edge cases (3.1–3.8): Improves signal correctness.
4. **Medium** – Data fetcher (4.1–4.8): Use `unittest.mock` for HTTP; `_convert_trade_history_to_ohlc` is pure logic.
5. **Low** – Integration (5.x): Requires more setup; add later.

---

## Implementation Notes

- **Models**: No mocks; direct `to_dict()` / `from_dict()` calls.
- **Data fetcher**: Extract `_convert_trade_history_to_ohlc` or call it with a list of dicts; no HTTP needed.
- **Firebase/Trader**: Use `pytest.fixture` with `unittest.mock.patch` for unit tests; avoid real API/Firebase in CI.

---

## Suggested New Test Files

```
tests/
├── test_models.py          # 2.1–2.6
├── test_indicator_edges.py # 1.1–1.8 (or merge into test_indicator_correctness.py)
├── test_strategy_edges.py  # 3.1–3.8 (or merge into test_new_strategy.py)
└── test_data_fetcher.py    # 4.1–4.8 (with mocked HTTP)
```
