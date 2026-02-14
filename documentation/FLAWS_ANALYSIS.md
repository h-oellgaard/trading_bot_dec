# Flaws Analysis - Trading Bot

## 🔴 KRITISKE FEJL (Must Fix)

### 1. **API Signature Generation Fejl** (trader.py:121)
**Problem**: Body serialisering er forkert for HMAC signature
```python
body = str(order_data).replace("'", '"')  # ❌ Forkert!
```
**Konsekvens**: API calls vil fejle med authentication errors
**Fix**: Brug `json.dumps()` med sorted keys for konsistent serialisering
```python
import json
body = json.dumps(order_data, sort_keys=True, separators=(',', ':'))
```

### 2. **Firebase Update Fejl** (firebase_store.py:86)
**Problem**: `update()` kræver at dokumentet eksisterer
```python
trade_ref.update(trade.to_dict())  # ❌ Fejler hvis dokument ikke eksisterer
```
**Konsekvens**: Trade updates vil fejle hvis dokumentet ikke findes
**Fix**: Brug `set()` med merge=True eller check eksistens først
```python
trade_ref.set(trade.to_dict(), merge=True)
```

### 3. **Profit/Loss Beregning Fejl** (main.py:114-119)
**Problem**: Profit/loss beregning for sell trades er forkert
```python
if trade.side == "buy":
    profit_loss = (close_price - trade.price) * trade.quantity
else:  # ❌ Dette er forkert for long positions
    profit_loss = (trade.price - close_price) * trade.quantity
```
**Konsekvens**: Forkerte P/L beregninger
**Fix**: For long positions (buy), profit er altid (close - entry) * quantity

### 4. **Close Trade Race Condition** (main.py:103-139)
**Problem**: Profit/loss beregnes først, derefter overskrives close_price
```python
profit_loss = (close_price - trade.price) * trade.quantity  # Beregnet med estimeret pris
...
sell_trade = self.trader.place_sell_order(...)
close_price = sell_trade.price  # Overskriver close_price!
# Men profit_loss er allerede beregnet med gammel pris
```
**Konsekvens**: Forkerte P/L tal i database
**Fix**: Beregn profit/loss EFTER faktisk execution

### 5. **None Return Type Handling** (strategy.py:69-72)
**Problem**: `get_latest_sma/ema` kan returnere None, men bruges uden check
```python
short_sma = get_latest_sma(candles, self.short_sma_period)  # Kan være None
long_sma = get_latest_sma(candles, self.long_sma_period)    # Kan være None
# Bruges senere uden None-check
```
**Konsekvens**: TypeError når der ikke er nok data
**Fix**: Check for None før brug

---

## 🟠 ALVORLIGE PROBLEMER (Should Fix)

### 6. **Signal Document ID Collision** (firebase_store.py:96)
**Problem**: Timestamp som document ID kan kollidere
```python
timestamp_str = signal.timestamp.isoformat()  # Kan være identisk for flere signals
signal_ref = self.db.collection("signals").document(timestamp_str)
```
**Konsekvens**: Nyere signals overskriver ældre hvis genereret samtidigt
**Fix**: Brug signal_id eller kombiner timestamp + signal_id

### 7. **Price Snapshot Document ID Collision** (firebase_store.py:157)
**Problem**: Samme issue med price snapshots
**Fix**: Brug timestamp + pair som ID, eller tillad duplicates

### 8. **Missing Input Validation**
**Problem**: Ingen validering af:
- quantity > 0
- price > 0
- balance >= minimum trade amount
- pair format
**Konsekvens**: Invalid trades kan blive placeret
**Fix**: Tilføj validering før API calls

### 9. **Missing Retry Logic**
**Problem**: Ingen retry mechanism ved API fejl
**Konsekvens**: Midlertidige netværksfejl stopper botten
**Fix**: Implementer exponential backoff retry

### 10. **Race Condition i Trade Execution** (main.py:247-267)
**Problem**: 
```python
open_trade = self.get_open_trade()  # Check 1
...
if signal.signal_type == SignalType.BUY and not open_trade:  # Check 2
    self.execute_buy_signal(signal)  # Mellem check 1 og 2 kunne trade være åbnet
```
**Konsekvens**: Flere trades kan åbnes samtidigt
**Fix**: Brug transaction eller lock mechanism

### 11. **Firestore Query Index Mangler**
**Problem**: Composite queries kræver indexes:
- `prices` collection: `pair` + `timestamp`
- `trades` collection: `pair` + `timestamp` (hvis både filters bruges)
**Konsekvens**: Queries fejler i produktion
**Fix**: Dokumenter nødvendige indexes eller opret dem automatisk

### 12. **Error Handling Swallows Exceptions**
**Problem**: Generiske Exception catches logger kun, fortsætter execution
```python
except Exception as e:
    logger.error(f"Error: {e}")  # Fortsætter som om intet er sket
    return False
```
**Konsekvens**: Kritiske fejl bliver ignoreret
**Fix**: Differentier mellem recoverable og fatal errors

---

## 🟡 MINDRE PROBLEMER (Nice to Fix)

### 13. **Hardcoded Minimum Trade Amount** (main.py:156)
```python
if balance_nok < 100:  # Hardcoded
```
**Fix**: Gør konfigurerbar via .env

### 14. **Missing Type Hints**
**Problem**: Nogle funktioner mangler return type hints
**Fix**: Tilføj komplette type hints

### 15. **Duplicate Code**
**Problem**: `_generate_signature` og `_get_headers` er duplikeret i både `data_fetcher.py` og `trader.py`
**Fix**: Opret base class eller shared utility module

### 16. **Inefficient Firebase Queries**
**Problem**: `get_all_trades` henter alle trades hver iteration
```python
all_trades = self.firebase.get_all_trades(pair=self.pair)  # Henter 1000 trades hver gang
```
**Fix**: Cache eller begræns query

### 17. **Missing Logging Context**
**Problem**: Logs mangler context (trade_id, signal_id, etc.)
**Fix**: Tilføj structured logging med context

### 18. **No Health Check**
**Problem**: Ingen måde at verificere at bot kører korrekt
**Fix**: Tilføj health check endpoint eller status file

### 19. **Missing Unit Tests**
**Problem**: Kun indicators har tests
**Fix**: Tilføj tests for strategy, trader, data_fetcher

### 20. **API Response Parsing Assumptions**
**Problem**: Koden antager specifik response format fra Firi API
```python
data.get("data", data.get("balances", []))  # Antager specifik struktur
```
**Konsekvens**: Fejler hvis API format ændres
**Fix**: Robust parsing med validation

### 21. **Timestamp Inconsistency**
**Problem**: Brug af `datetime.now()` i flere moduler kan give forskellige timestamps
**Fix**: Centraliser timestamp generation

### 22. **Missing Connection Pooling**
**Problem**: Ny httpx client hver request
**Fix**: Brug persistent client med connection pooling

### 23. **No Rate Limiting**
**Problem**: Ingen rate limiting på API calls
**Konsekvens**: Kan overskride API limits
**Fix**: Implementer rate limiter

### 24. **Firebase Credentials Handling** (firebase_store.py:26)
**Problem**: Overskriver environment variable
```python
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
```
**Konsekvens**: Kan påvirke andre Firebase clients
**Fix**: Brug explicit credentials parameter

---

## 📋 SAMMENFATNING

### Kritiske Fejl: 5
### Alvorlige Problemer: 7
### Mindre Problemer: 12

### Prioriteret Fix Rækkefølge:
1. Fix API signature generation (trader.py)
2. Fix Firebase update method
3. Fix profit/loss calculation
4. Fix close trade logic
5. Add None checks for indicators
6. Fix document ID collisions
7. Add input validation
8. Add retry logic
9. Fix race conditions
10. Document/create Firestore indexes










