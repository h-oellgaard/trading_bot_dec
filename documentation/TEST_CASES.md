# Test Cases - Firi Trading Bot

## 1. Indicators Module Tests

### TC-001: EMA Calculation - Sufficient Data
**Beskrivelse:** Beregn EMA med tilstrækkelig data (>= period)
**Input:** 50 candles, period=20
**Forventet:** Liste med 20 None-værdier + 30 EMA-værdier

### TC-002: EMA Calculation - Insufficient Data
**Beskrivelse:** Beregn EMA med utilstrækkelig data (< period)
**Input:** 10 candles, period=20
**Forventet:** Liste med 10 None-værdier

### TC-003: EMA Crossover Detection - Golden Cross
**Beskrivelse:** Detekter når short EMA krydser over long EMA
**Input:** Candles hvor short_ema[-2] < long_ema[-2] og short_ema[-1] > long_ema[-1]
**Forventet:** True

### TC-004: EMA Below EMA for Periods
**Beskrivelse:** Tjek om short EMA har været under medium EMA i 3 perioder
**Input:** Candles hvor short < medium i sidste 3 candles
**Forventet:** True

### TC-005: EMA Above EMA for Periods
**Beskrivelse:** Tjek om medium EMA har været over long EMA i 3 perioder
**Input:** Candles hvor medium > long i sidste 3 candles
**Forventet:** True

## 2. Strategy Module Tests

### TC-006: Generate BUY Signal - Valid Conditions
**Beskrivelse:** Generer BUY signal når medium EMA > long EMA i 3 perioder
**Input:** Candles med medium > long i 3 perioder, ingen åben trade, ikke i cooldown
**Forventet:** SignalType.BUY med korrekt reason og medium_ema værdi

### TC-007: Generate SELL Signal - Valid Conditions
**Beskrivelse:** Generer SELL signal når short EMA < medium EMA i 3 perioder
**Input:** Candles med short < medium i 3 perioder, åben trade eksisterer
**Forventet:** SignalType.SELL med korrekt reason og alle EMA værdier

### TC-008: Generate HOLD Signal - Insufficient Data
**Beskrivelse:** Generer HOLD signal når der ikke er nok candles
**Input:** Færre candles end long_ema_period + 3
**Forventet:** SignalType.HOLD med reason "Insufficient data"

### TC-009: Generate HOLD Signal - In Cooldown
**Beskrivelse:** Generer HOLD signal når i cooldown periode
**Input:** Valid BUY conditions men in_cooldown=True
**Forventet:** SignalType.HOLD med reason "In cooldown period"

### TC-010: Generate HOLD Signal - No Conditions Met
**Beskrivelse:** Generer HOLD signal når ingen signal betingelser er opfyldt
**Input:** Candles hvor ingen crossover eller period-betingelser er opfyldt
**Forventet:** SignalType.HOLD med reason "No signal conditions met"

### TC-011: Trailing Stop Loss - Trigger Condition
**Beskrivelse:** Tjek om trailing stop loss skal triggere (7% drop fra højeste)
**Input:** Entry=100, highest=110, current=102.3 (7% drop)
**Forventet:** (True, 110)

### TC-012: Trailing Stop Loss - No Trigger
**Beskrivelse:** Tjek om trailing stop loss ikke skal triggere
**Input:** Entry=100, highest=110, current=105 (kun 4.5% drop)
**Forventet:** (False, 110)

## 3. Data Fetcher Module Tests

### TC-013: Fetch Candles - Trade History Conversion
**Beskrivelse:** Hent candles fra API og konverter trade history til OHLC
**Input:** API returnerer 100 trades med created_at, price, amount
**Forventet:** Liste af Candle objekter med korrekt OHLC for 30-min intervaller

### TC-014: Fetch Candles - Multiple Market Formats
**Beskrivelse:** Prøv forskellige market formats hvis første fejler
**Input:** ETHDKK returnerer 404, prøv ETH-DKK, ethdkk, etc.
**Forventet:** Succes med en af formatene eller exception hvis alle fejler

### TC-015: Fetch Candles - Handle Created_at Timestamps
**Beskrivelse:** Parse ISO format timestamps fra trade history
**Input:** Trade med created_at='2025-12-03T18:49:00.922Z'
**Forventet:** Korrekt datetime objekt

### TC-016: Get Current Price - Success
**Beskrivelse:** Hent seneste pris for et trading pair
**Input:** ETH/DKK, interval=1m, limit=1
**Forventet:** Float værdi med seneste close price

### TC-017: Get Current Price - No Data
**Beskrivelse:** Håndter tilfælde hvor ingen data er tilgængelig
**Input:** Invalid pair eller API fejl
**Forventet:** None

## 4. Firebase Store Module Tests

### TC-018: Save and Retrieve Trade
**Beskrivelse:** Gem trade i Firestore og hent den igen
**Input:** Trade objekt med status=OPEN
**Forventet:** Trade kan hentes med get_trade() og har samme data

### TC-019: Get Open Trades - With Pair Filter
**Beskrivelse:** Hent alle åbne trades for et specifikt pair
**Input:** 3 open trades, 2 for ETH/DKK, 1 for ETH/NOK, pair='ETH/DKK'
**Forventet:** 2 trades returneret

### TC-020: Get Price Snapshots - Ordering
**Beskrivelse:** Hent price snapshots sorteret korrekt
**Input:** 100 price snapshots i Firebase
**Forventet:** Liste sorteret efter timestamp (oldest first)

## 5. Integration Tests

### TC-021: Full Trading Cycle - Buy to Sell
**Beskrivelse:** Simuler komplet trading cyklus fra BUY til SELL
**Input:** Candles der trigger BUY, derefter SELL betingelser
**Forventet:** Trade oprettet, derefter lukket med korrekt P/L beregning

### TC-022: Portfolio State Update
**Beskrivelse:** Opdater portfolio state med korrekte værdier
**Input:** Balance, open trades, closed trades
**Forventet:** PortfolioState med korrekt total_value og profit/loss

### TC-023: Initialize with Firebase Data
**Beskrivelse:** Load initial candles fra Firebase hvis tilgængelige
**Input:** 100 candles i Firebase for pair
**Forventet:** Bruger Firebase data, opdaterer med API data

### TC-024: Initialize without Firebase Data
**Beskrivelse:** Load initial candles fra API hvis Firebase er tom
**Input:** Ingen candles i Firebase
**Forventet:** Henter 100 candles fra API og gemmer i Firebase

## 6. Error Handling Tests

### TC-025: API Authentication Failure
**Beskrivelse:** Håndter fejl ved API autentificering
**Input:** Invalid API key eller secret
**Forventet:** Exception med beskrivende fejlbesked

### TC-026: Firebase Connection Failure
**Beskrivelse:** Håndter fejl ved Firebase forbindelse
**Input:** Invalid credentials eller network error
**Forventet:** Exception ved initialization, graceful degradation

### TC-027: Insufficient Balance for Trade
**Beskrivelse:** Håndter tilfælde hvor der ikke er nok balance
**Input:** BUY signal men balance < required amount
**Forventet:** Warning log, ingen trade oprettet

### TC-028: Invalid Candle Data
**Beskrivelse:** Håndter korrupt eller manglende candle data
**Input:** Candle med None værdier eller manglende felter
**Forventet:** Skip invalid candles, continue processing

## 7. Edge Cases

### TC-029: Cooldown Period Calculation
**Beskrivelse:** Beregn cooldown korrekt baseret på candle interval
**Input:** Sell trade closed 25 timer siden, 30-min candles
**Forventet:** in_cooldown=True hvis < 25 candles, False hvis >= 25

### TC-030: Multiple Signals in Same Iteration
**Beskrivelse:** Håndter tilfælde hvor både BUY og SELL conditions er opfyldt
**Input:** Candles der opfylder både BUY og SELL betingelser
**Forventet:** SELL har prioritet hvis åben trade eksisterer


