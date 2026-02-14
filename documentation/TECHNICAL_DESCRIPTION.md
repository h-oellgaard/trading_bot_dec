# Teknisk Beskrivelse - Firi Trading Bot

## Systemarkitektur

Firi Trading Bot er en automatiseret cryptocurrency trading bot bygget i Python, der handler BTC/DKK via Firi API og gemmer alle data i Firebase Firestore. Systemet følger GRASP-principper og Separation of Concerns med en modulær arkitektur.

**Kernemoduler:**
- `data_fetcher.py`: Henter OHLC candle data fra Firi API v2/markets/{market}/history endpoint. Konverterer trade history til OHLC candles med 30-minutters intervaller ved at gruppere trades og beregne open, high, low, close og volume for hvert interval.
- `indicators.py`: Pure functions til beregning af tekniske indikatorer (SMA, EMA) uden side effects. Implementerer crossover detection og period-baserede sammenligninger.
- `strategy.py`: TradingStrategy klasse der implementerer en tre-EMA strategi. Genererer BUY signals når medium EMA (20) går over long EMA (50) i 3 på hinanden følgende candles, og SELL signals når short EMA (10) går under medium EMA i 3 candles. Inkluderer trailing stop-loss logik (7% fra højeste pris).
- `trader.py`: FiriTrader klasse der håndterer HMAC-baseret autentificering og order execution via Firi API v2. Implementerer buy/sell orders med korrekt signature generation.
- `firebase_store.py`: Firebase Firestore integration med CRUD operationer for trades, signals, portfolio state og price snapshots. Bruger composite indexes for effektive queries.
- `main.py`: TradingBot orchestrator der kører kontinuerlig loop hver 30. minut. Initialiserer med 100 historiske candles, genererer signals, eksekverer trades og opdaterer portfolio state.

**Dataflow:** API → Data Fetcher → Indicators → Strategy → Trader → Firebase Store. Systemet håndterer cooldown perioder (25 candles efter sell), trailing stop-loss og sikrer max ét åbent trade ad gangen.


