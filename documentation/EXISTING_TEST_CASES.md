# 20 Eksisterende Test Cases - Firi Trading Bot

Dette dokument lister de 20 test cases der allerede er implementeret i projektet.

## Indicators Module (8 test cases)

### 1. `test_calculate_sma`
**Fil:** `test_indicators.py:38-53`  
**Beskrivelse:** Test SMA beregning med tilstrækkelig data  
**Assertions:**
- Første `period-1` værdier skal være `None`
- Første SMA værdi skal være gennemsnit af første `period` closes
- Alle efterfølgende værdier skal være beregnet

### 2. `test_calculate_ema`
**Fil:** `test_indicators.py:56-71`  
**Beskrivelse:** Test EMA beregning med tilstrækkelig data  
**Assertions:**
- Første `period-1` værdier skal være `None`
- Første EMA værdi skal være lig med SMA
- Alle efterfølgende værdier skal være beregnet

### 3. `test_get_latest_sma`
**Fil:** `test_indicators.py:74-80`  
**Beskrivelse:** Test at hente seneste SMA værdi  
**Assertions:**
- Returnerer ikke-None værdi
- Returnerer float type

### 4. `test_get_latest_ema`
**Fil:** `test_indicators.py:83-89`  
**Beskrivelse:** Test at hente seneste EMA værdi  
**Assertions:**
- Returnerer ikke-None værdi
- Returnerer float type

### 5. `test_sma_crossover`
**Fil:** `test_indicators.py:92-102`  
**Beskrivelse:** Test SMA crossover detection  
**Assertions:**
- Returnerer boolean værdi
- Fungerer når der er nok candles

### 6. `test_ema_below_sma_for_periods`
**Fil:** `test_indicators.py:105-112`  
**Beskrivelse:** Test om EMA har været under SMA i flere perioder  
**Assertions:**
- Returnerer boolean værdi

### 7. `test_ema_above_ema_for_periods`
**Fil:** `test_indicators.py:115-122`  
**Beskrivelse:** Test om medium EMA har været over long EMA i flere perioder  
**Assertions:**
- Returnerer boolean værdi

### 8. `test_insufficient_data`
**Fil:** `test_indicators.py:125-140`  
**Beskrivelse:** Test adfærd med utilstrækkelig data  
**Assertions:**
- Alle SMA værdier skal være `None` når data er utilstrækkelig
- Alle EMA værdier skal være `None` når data er utilstrækkelig

## Strategy Module (12 test cases)

### 9. `test_buy_signal_when_medium_above_long_for_3_periods`
**Fil:** `test_new_strategy.py:37-65`  
**Beskrivelse:** Test BUY signal generation når medium EMA > long EMA i 3 perioder  
**GIVEN:** Stærk uptrend (monotonisk stigende priser)  
**WHEN:** Ingen åben trade  
**THEN:** Strategy skal producere BUY signal  
**Assertions:**
- `signal.signal_type == SignalType.BUY`
- `signal.reason` indeholder "Medium EMA" eller "medium EMA"

### 10. `test_sell_signal_when_short_below_medium_for_3_periods`
**Fil:** `test_new_strategy.py:68-96`  
**Beskrivelse:** Test SELL signal generation når short EMA < medium EMA i 3 perioder  
**GIVEN:** Klar downtrend (monotonisk faldende priser)  
**WHEN:** Åben trade eksisterer  
**THEN:** Strategy skal producere SELL signal  
**Assertions:**
- `signal.signal_type == SignalType.SELL`
- `signal.reason` indeholder "Short EMA" eller "short EMA"

### 11. `test_hold_when_no_buy_or_sell_conditions_are_met`
**Fil:** `test_new_strategy.py:99-127`  
**Beskrivelse:** Test HOLD signal når ingen klare trends  
**GIVEN:** Choppy, sideways market (ingen klar trend)  
**WHEN:** Enten åben eller ingen åben trade  
**THEN:** Strategy skal returnere HOLD  
**Assertions:**
- `signal.signal_type == SignalType.HOLD`
- `signal.reason` indeholder "No signal", "Insufficient", eller "conditions met"

### 12. `test_buy_signal_blocked_during_cooldown`
**Fil:** `test_new_strategy.py:130-150`  
**Beskrivelse:** Test at BUY signal blokeres under cooldown  
**GIVEN:** Medium EMA > long EMA for 3 perioder (BUY condition opfyldt)  
**WHEN:** I cooldown periode  
**THEN:** Strategy skal returnere HOLD i stedet for BUY  
**Assertions:**
- `signal.signal_type == SignalType.HOLD`
- `signal.reason` indeholder "cooldown" eller "Cooldown"

### 13. `test_trailing_stop_not_triggered_above_threshold`
**Fil:** `test_new_strategy.py:153-173`  
**Beskrivelse:** Test at trailing stop ikke trigger når drop < 7%  
**GIVEN:** `highest_price = 120`, trailing 7%  
**WHEN:** `current_price = 115` (drop < 7%)  
**THEN:** Trailing stop skal IKKE trigger  
**Assertions:**
- `should_trigger == False`
- `new_highest == highest` (uændret)

### 14. `test_trailing_stop_triggers_below_threshold`
**Fil:** `test_new_strategy.py:176-196`  
**Beskrivelse:** Test at trailing stop trigger når drop > 7%  
**GIVEN:** `highest_price = 120`, trailing 7%  
**WHEN:** `current_price = 111` (drop > 7%)  
**THEN:** Trailing stop SKAL trigger  
**Assertions:**
- `should_trigger == True`
- `new_highest == highest` (uændret før update)

### 15. `test_trailing_stop_updates_highest_price`
**Fil:** `test_new_strategy.py:199-219`  
**Beskrivelse:** Test at trailing stop opdaterer highest price ved nye highs  
**GIVEN:** `highest_price = 120`  
**WHEN:** `current_price = 125` (nyt high)  
**THEN:** `highest_price` skal opdateres til 125  
**Assertions:**
- `should_trigger == False`
- `new_highest == 125.0`

### 16. `test_insufficient_data_returns_hold`
**Fil:** `test_new_strategy.py:222-241`  
**Beskrivelse:** Test at utilstrækkelig data returnerer HOLD  
**GIVEN:** Utilstrækkelig candles til EMA beregning  
**WHEN:** Genererer signal  
**THEN:** Strategy skal returnere HOLD med "Insufficient data" reason  
**Assertions:**
- `signal.signal_type == SignalType.HOLD`
- `"Insufficient" in signal.reason`

### 17. `test_sell_signal_only_when_has_open_trade`
**Fil:** `test_new_strategy.py:244-263`  
**Beskrivelse:** Test at SELL signal kun genereres når åben trade eksisterer  
**GIVEN:** Short EMA < medium EMA for 3 perioder  
**WHEN:** Ingen åben trade  
**THEN:** Strategy skal IKKE producere SELL signal  
**Assertions:**
- `signal.signal_type != SignalType.SELL`

### 18. `test_buy_signal_only_when_no_open_trade`
**Fil:** `test_new_strategy.py:266-285`  
**Beskrivelse:** Test at BUY signal kun genereres når ingen åben trade  
**GIVEN:** Medium EMA > long EMA for 3 perioder  
**WHEN:** Åben trade eksisterer  
**THEN:** Strategy skal IKKE producere BUY signal  
**Assertions:**
- `signal.signal_type != SignalType.BUY`

### 19. `test_cooldown_logic`
**Fil:** `test_new_strategy.py:288-313`  
**Beskrivelse:** Test cooldown logik baseret på antal candles  
**Beskrivelse:** Test at cooldown forhindrer køb i N candles efter et salg  
**Test Cases:**
- Med nok candles efter sell: cooldown skal være `False`
- Med få candles efter sell: cooldown skal være `True`  
**Assertions:**
- `candles_after_sell >= cooldown_candles` for første case
- `candles_after_sell_early < cooldown_candles` for anden case

## Test Coverage Summary

**Total:** 20 test cases
- **Indicators Module:** 8 test cases
- **Strategy Module:** 12 test cases

**Test Runner:** pytest  
**Fixtures:** `sample_candles` (test_indicators.py), `make_candles_from_prices` helper (test_new_strategy.py)

## Kørsel af Tests

```bash
# Kør alle tests
pytest

# Kør kun indicators tests
pytest test_indicators.py

# Kør kun strategy tests
pytest test_new_strategy.py

# Kør med verbose output
pytest -v

# Kør med coverage
pytest --cov=. --cov-report=html
```


