# BotAgain Trading Bot - Architecture Diagram

## System Architecture Overview

This document provides a visual representation of the BotAgain trading bot architecture.

## Component Architecture

```mermaid
graph TB
    subgraph "External Services"
        FIRI[Firi API<br/>Trading & Market Data]
        FIREBASE[Firebase Firestore<br/>Data Persistence]
    end

    subgraph "Trading Bot Application"
        MAIN[TradingBot<br/>main.py<br/>Orchestrator]
        
        subgraph "Data Layer"
            FETCHER[FiriDataFetcher<br/>data_fetcher.py<br/>- Fetch OHLC candles<br/>- Get current price<br/>- Convert trade history to OHLC]
            STORE[FirebaseStore<br/>firebase_store.py<br/>- Save/retrieve trades<br/>- Save/retrieve signals<br/>- Save portfolio state<br/>- Save price snapshots]
        end
        
        subgraph "Analysis Layer"
            INDICATORS[Indicators<br/>indicators.py<br/>Pure Functions<br/>- SMA calculation<br/>- EMA calculation<br/>- Crossover detection<br/>- Period-based comparisons]
            STRATEGY[TradingStrategy<br/>strategy.py<br/>- 3-EMA strategy<br/>- Signal generation<br/>- Trailing stop-loss logic]
        end
        
        subgraph "Execution Layer"
            TRADER[FiriTrader<br/>trader.py<br/>- HMAC authentication<br/>- Place buy/sell orders<br/>- Get balances<br/>- Order management]
        end
        
        subgraph "Data Models"
            MODELS[Models<br/>models.py<br/>- Candle<br/>- Trade<br/>- Signal<br/>- PortfolioState]
        end
    end

    %% Data Flow
    MAIN --> FETCHER
    MAIN --> INDICATORS
    MAIN --> STRATEGY
    MAIN --> TRADER
    MAIN --> STORE
    
    FETCHER --> FIRI
    FETCHER --> MODELS
    
    INDICATORS --> MODELS
    STRATEGY --> INDICATORS
    STRATEGY --> MODELS
    
    TRADER --> FIRI
    TRADER --> MODELS
    
    STORE --> FIREBASE
    STORE --> MODELS
    
    %% Styling
    classDef external fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef orchestrator fill:#fff3e0,stroke:#e65100,stroke-width:3px
    classDef data fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef analysis fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef execution fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef models fill:#f5f5f5,stroke:#424242,stroke-width:2px
    
    class FIRI,FIREBASE external
    class MAIN orchestrator
    class FETCHER,STORE data
    class INDICATORS,STRATEGY analysis
    class TRADER execution
    class MODELS models
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant Bot as TradingBot
    participant Fetcher as FiriDataFetcher
    participant API as Firi API
    participant Indicators as Indicators
    participant Strategy as TradingStrategy
    participant Trader as FiriTrader
    participant Store as FirebaseStore
    participant Firebase as Firestore

    Note over Bot: Initialization (100 candles)
    Bot->>Store: Get price snapshots from Firebase
    alt Not enough data in Firebase
        Bot->>Fetcher: Fetch candles from API
        Fetcher->>API: GET /v2/markets/{market}/history
        API-->>Fetcher: Trade history or OHLC data
        Fetcher-->>Bot: List of Candle objects
        Bot->>Store: Save candles to Firebase
        Store->>Firebase: Store price snapshots
    end

    loop Every 30 minutes
        Note over Bot: Main Trading Loop
        
        Bot->>Fetcher: Get candles (100 candles, 30m interval)
        Fetcher->>API: GET /v2/markets/{market}/history
        API-->>Fetcher: OHLC data
        Fetcher-->>Bot: List of Candle objects
        Bot->>Store: Save latest price snapshot
        
        Bot->>Store: Get open trades
        Store->>Firebase: Query open trades
        Firebase-->>Store: Open trades
        Store-->>Bot: Open trade (if any)
        
        alt Open trade exists
            Bot->>Strategy: Check trailing stop-loss
            Strategy-->>Bot: Should trigger stop-loss?
            alt Stop-loss triggered
                Bot->>Trader: Place sell order
                Trader->>API: POST /v2/orders (ask)
                API-->>Trader: Order confirmation
                Trader-->>Bot: Trade object
                Bot->>Store: Save closed trade
            end
        end
        
        Bot->>Store: Check cooldown period
        Store->>Firebase: Get recent closed trades
        Firebase-->>Store: Recent trades
        Store-->>Bot: Cooldown status
        
        Bot->>Strategy: Generate signal
        Strategy->>Indicators: Calculate EMAs (10, 20, 50)
        Indicators-->>Strategy: EMA values
        Strategy->>Indicators: Check crossover conditions
        Indicators-->>Strategy: Crossover status
        Strategy-->>Bot: Signal (BUY/SELL/HOLD)
        
        Bot->>Store: Save signal
        Store->>Firebase: Store signal
        
        alt BUY signal and no open trade
            Bot->>Trader: Get balance (DKK)
            Trader->>API: GET /v2/balances
            API-->>Trader: Balance data
            Trader-->>Bot: Available balance
            Bot->>Trader: Place buy order
            Trader->>API: POST /v2/orders (bid)
            API-->>Trader: Order confirmation
            Trader-->>Bot: Trade object
            Bot->>Store: Save trade
        else SELL signal and open trade
            Bot->>Trader: Place sell order
            Trader->>API: POST /v2/orders (ask)
            API-->>Trader: Order confirmation
            Trader-->>Bot: Trade object
            Bot->>Store: Save closed trade
        end
        
        Bot->>Trader: Get balances (BTC, DKK)
        Trader->>API: GET /v2/balances
        API-->>Trader: Balance data
        Trader-->>Bot: Balances
        Bot->>Fetcher: Get current price
        Fetcher->>API: GET current price
        API-->>Fetcher: Current price
        Fetcher-->>Bot: Current price
        Bot->>Store: Update portfolio state
        Store->>Firebase: Store portfolio state
    end
```

## Module Dependencies

```mermaid
graph LR
    subgraph "Core Modules"
        MAIN[main.py]
        MODELS[models.py]
    end
    
    subgraph "Data Modules"
        FETCHER[data_fetcher.py]
        STORE[firebase_store.py]
    end
    
    subgraph "Analysis Modules"
        INDICATORS[indicators.py]
        STRATEGY[strategy.py]
    end
    
    subgraph "Execution Module"
        TRADER[trader.py]
    end
    
    MAIN --> MODELS
    MAIN --> FETCHER
    MAIN --> STORE
    MAIN --> INDICATORS
    MAIN --> STRATEGY
    MAIN --> TRADER
    
    FETCHER --> MODELS
    STORE --> MODELS
    INDICATORS --> MODELS
    STRATEGY --> MODELS
    STRATEGY --> INDICATORS
    TRADER --> MODELS
```

## Trading Strategy Logic

```mermaid
flowchart TD
    START([Start Trading Loop]) --> FETCH[Fetch 100 Candles<br/>30-minute interval]
    FETCH --> CHECK_OPEN{Open Trade<br/>Exists?}
    
    CHECK_OPEN -->|Yes| CHECK_STOP[Check Trailing<br/>Stop-Loss 7%]
    CHECK_STOP -->|Triggered| SELL_STOP[Execute Sell Order]
    SELL_STOP --> CHECK_COOLDOWN
    CHECK_STOP -->|Not Triggered| CHECK_COOLDOWN
    
    CHECK_OPEN -->|No| CHECK_COOLDOWN[Check Cooldown<br/>25 candles after sell]
    
    CHECK_COOLDOWN -->|In Cooldown| HOLD[Generate HOLD Signal]
    CHECK_COOLDOWN -->|Not in Cooldown| CALC_INDICATORS[Calculate EMAs<br/>Short: 10, Medium: 20, Long: 50]
    
    CALC_INDICATORS --> CHECK_SELL{Short EMA < Medium EMA<br/>for 3 candles?}
    CHECK_SELL -->|Yes & Open Trade| SELL[Generate SELL Signal<br/>Execute Sell Order]
    
    CHECK_SELL -->|No| CHECK_BUY{Medium EMA > Long EMA<br/>for 3 candles?}
    CHECK_BUY -->|Yes & No Open Trade| BUY[Generate BUY Signal<br/>Execute Buy Order]
    CHECK_BUY -->|No| HOLD
    
    SELL --> UPDATE_PORTFOLIO[Update Portfolio State]
    BUY --> UPDATE_PORTFOLIO
    HOLD --> UPDATE_PORTFOLIO
    
    UPDATE_PORTFOLIO --> SAVE_DATA[Save to Firebase:<br/>- Signals<br/>- Trades<br/>- Portfolio State<br/>- Price Snapshots]
    SAVE_DATA --> WAIT[Wait 30 minutes]
    WAIT --> START
    
    style START fill:#e1f5ff
    style SELL fill:#ffebee
    style BUY fill:#e8f5e9
    style HOLD fill:#fff3e0
    style UPDATE_PORTFOLIO fill:#f3e5f5
```

## Data Storage Structure

```mermaid
erDiagram
    TRADES ||--o{ SIGNALS : generates
    TRADES ||--o{ PORTFOLIO : affects
    PRICE_SNAPSHOTS ||--o{ SIGNALS : used_for
    
    TRADES {
        string trade_id PK
        string pair
        string side
        float price
        float quantity
        string status
        datetime timestamp
        float highest_price
        float close_price
        datetime close_timestamp
        float profit_loss
        float profit_loss_percent
    }
    
    SIGNALS {
        string signal_id PK
        string signal_type
        datetime timestamp
        float price
        float short_ema
        float medium_ema
        float long_ema
        string reason
    }
    
    PORTFOLIO {
        datetime timestamp PK
        float balance_nok
        float balance_btc
        float total_value_nok
        int open_trades_count
        int closed_trades_count
        float total_profit_loss
        float total_profit_loss_percent
    }
    
    PRICE_SNAPSHOTS {
        string doc_id PK
        string pair
        datetime timestamp
        float open
        float high
        float low
        float close
        float volume
    }
```

## Key Architectural Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Pure Functions**: Indicator calculations are side-effect-free and fully testable
3. **Data Models**: Centralized data structures in `models.py` ensure consistency
4. **GRASP Principles**: Following Information Expert, Creator, and Controller patterns
5. **Modularity**: Components can be tested and modified independently
6. **External Dependencies**: Clear boundaries with Firi API and Firebase Firestore

## Component Responsibilities

| Component | Responsibility | Key Methods |
|-----------|---------------|-------------|
| **TradingBot** | Orchestrates the trading loop, coordinates all components | `run()`, `run_iteration()`, `initialize()` |
| **FiriDataFetcher** | Fetches market data from Firi API, converts to OHLC format | `get_candles()`, `get_current_price()` |
| **Indicators** | Pure functions for technical indicator calculations | `calculate_ema()`, `ema_above_ema_for_periods()` |
| **TradingStrategy** | Implements trading logic, generates signals | `generate_signal()`, `should_trailing_stop_loss()` |
| **FiriTrader** | Executes trades via Firi API with HMAC authentication | `place_buy_order()`, `place_sell_order()`, `get_balance()` |
| **FirebaseStore** | Persists all data to Firestore | `save_trade()`, `save_signal()`, `save_portfolio_state()` |
| **Models** | Data structures for trades, signals, candles, portfolio | `Trade`, `Signal`, `Candle`, `PortfolioState` |
