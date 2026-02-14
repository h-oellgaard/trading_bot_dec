# 🔴 KRITISKE FEJL DER SKAL FIXES NU

## Top 5 Kritiske Fejl

### 1. API Signature Fejl (trader.py:121)
**Status**: ❌ BRUDER API AUTHENTICATION
```python
# NUVÆRENDE (FORKERT):
body = str(order_data).replace("'", '"')

# SKAL VÆRE:
import json
body = json.dumps(order_data, sort_keys=True, separators=(',', ':'))
```

### 2. Firebase Update Fejl (firebase_store.py:86)
**Status**: ❌ FEJLER HVIS DOKUMENT IKKE EKSISTERER
```python
# NUVÆRENDE (FORKERT):
trade_ref.update(trade.to_dict())

# SKAL VÆRE:
trade_ref.set(trade.to_dict(), merge=True)
```

### 3. Profit/Loss Beregning (main.py:114-119)
**Status**: ❌ FORKERTE P/L TAL
```python
# NUVÆRENDE (FORKERT):
if trade.side == "buy":
    profit_loss = (close_price - trade.price) * trade.quantity
else:
    profit_loss = (trade.price - close_price) * trade.quantity  # ❌ Forkert!

# SKAL VÆRE (for long positions):
profit_loss = (close_price - trade.price) * trade.quantity  # Altid samme formel
```

### 4. Close Trade Logic (main.py:122-124)
**Status**: ❌ P/L BEREGNES MED FORKERT PRIS
```python
# NUVÆRENDE (FORKERT):
profit_loss = (close_price - trade.price) * trade.quantity  # Beregnet først
sell_trade = self.trader.place_sell_order(...)
close_price = sell_trade.price  # Overskriver, men P/L allerede beregnet!

# SKAL VÆRE:
sell_trade = self.trader.place_sell_order(...)
close_price = sell_trade.price  # Faktisk executed price
profit_loss = (close_price - trade.price) * trade.quantity  # Beregn EFTER execution
```

### 5. None Return Handling (strategy.py:69-90)
**Status**: ❌ CRASHER VED MANGLENDE DATA
```python
# NUVÆRENDE (FORKERT):
short_sma = get_latest_sma(candles, self.short_sma_period)  # Kan være None
# Bruges senere uden check → TypeError

# SKAL VÆRE:
short_sma = get_latest_sma(candles, self.short_sma_period)
if short_sma is None or long_sma is None:
    return Signal(..., signal_type=SignalType.HOLD, reason="Insufficient data")
```

---

## Quick Fix Checklist

- [ ] Fix API signature i `trader.py` (linje 121)
- [ ] Fix Firebase update i `firebase_store.py` (linje 86)
- [ ] Fix P/L beregning i `main.py` (linje 114-119)
- [ ] Fix close trade sequence i `main.py` (linje 122-124)
- [ ] Tilføj None checks i `strategy.py` (linje 69-90)
- [ ] Test API authentication virker
- [ ] Test trade execution virker
- [ ] Test P/L beregninger er korrekte

---

## Test Efter Fixes

```bash
# Test API connection
python -c "from trader import FiriTrader; t = FiriTrader(); print(t.get_balance('NOK'))"

# Test indicators
pytest test_indicators.py -v

# Test strategy med edge cases
python -c "from strategy import TradingStrategy; from models import Candle; ..."
```

---

**⚠️ VIGTIGT**: Disse fejl vil forhindre botten i at fungere korrekt i produktion. Fix dem FØR deployment!










