# ⚙️ Arkitekturprincipper for Crypto Trading Bot

Dette dokument beskriver retningslinjer for udviklingen af en Python-baseret crypto trading bot. Målet er at opnå **høj kvalitet, lav kobling, høj testbarhed** og mulighed for nem videreudvikling.

---

## ✅ Designprincipper

### Separation of Concerns (SoC)
- Hold ansvar adskilt: data, strategi, execution og persistens skal være i egne moduler.
- Undgå at blande logik og I/O (ingen print eller filadgang i strategikoden).

### GRASP-principper
- **Information Expert**: Placer ansvar der, hvor data er tilgængelig.
- **Low Coupling**: Komponenter skal kunne ændres uafhængigt.
- **High Cohesion**: Klasser skal kun gøre det, de er bedst til.
- **Creator**: Den klasse, der har flest oplysninger om et objekt, bør oprette det.

---

## 🧱 Arkitekturkrav

### 1. Coin-objekt
```python
class Coin:
    def __init__(self, symbol: str, name: str, precision: int):
        self.symbol = symbol
        self.name = name
        self.precision = precision
```
- Ingen direkte afhængighed til exchange.

### 2. Handelser og gemning
- Brug `Trade`-klasser til at repræsentere handler:
```python
class Trade:
    def __init__(self, coin: Coin, action: str, amount: float, price: float, timestamp: datetime):
        ...
```
- Persistér via `TradeRepository` (fil, SQLite, memory).

### 3. Strategi-mønster
- Implementér strategi som klasse med `generate_signal(market_data)`:
```python
class TradingStrategy(ABC):
    @abstractmethod
    def generate_signal(self, market_data: MarketData) -> Optional[str]:
        ...
```

### 4. Testbarhed
- Brug **dependency injection** for at isolere tests.
- Al forretningslogik skal kunne enhedstestes.
- Tilføj integrationstests for end-to-end flow.

---

## 🔄 Iterationsprincipper

Når første løsning er på plads:
1. Gennemgå og refaktorér for:
   - Navngivning
   - Ansvarsfordeling
   - Fjernelse af duplikering
2. Forbedr ud fra:
   - **SOLID-principper**
   - Interface-orienteret design
   - Klar opdeling mellem domæne og infrastruktur

---

## 🧪 Eksempel på testbar struktur

```python
# tests/test_sma_cross.py

def test_sma_cross_buy_signal():
    strategy = SmaCrossStrategy(short=3, long=5)
    market_data = [100, 102, 104, 103, 106]  # Eksempeldata
    signal = strategy.generate_signal(market_data)
    assert signal == "BUY"
```

---

## 🛠️ Teknologi-stack

- Python 3.11+
- SQLite (eller filbaseret persistens)
- Pytest til test
- Modular design
- Valgfri: REST API, WebSocket, CLI, Discord/Telegram bots

---

> 📌 Brug dette dokument som udgangspunkt for udvikling, review og iteration. Alle kodeforslag skal være testbare og så vidt muligt ikke kræve ændringer i andre moduler.