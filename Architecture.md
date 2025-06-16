# 🧠 Crypto Trading Bot – Arkitektur

Dette dokument beskriver arkitekturen for en modulær Python-baseret crypto trading bot, designet med fleksibilitet og udvidelsesmuligheder i tankerne. Botten understøtter fx Firi eller Binance som exchanges og er klar til at integrere tekniske indikatorer, AI-strategier og CLI-styring.

## 🎯 Arkitekturdiagram

```mermaid
flowchart TB
  config["Config & ENV"]
  exchange["Exchange Adapter\n(Firi, Binance...)"]
  market_data["Market Data Module"]
  strategy["Strategy Engine\n(SMA, EMA, AI)"]
  execution["Trade Execution"]
  logger["Logger & DB"]
  cli["CLI / Scheduler"]

  config --> exchange
  exchange --> market_data
  market_data --> strategy
  strategy --> execution
  execution --> logger
  logger --> cli
