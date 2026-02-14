# Firi Trading Bot

En komplet Python-trading bot der handler via Firi API og gemmer alle data i Firebase Firestore.

## Arkitektur

Projektet følger GRASP-principper og Separation of Concerns:

- **data_fetcher.py** - Henter OHLC-priser fra Firi API
- **indicators.py** - Beregner SMA og EMA (pure functions)
- **strategy.py** - Implementerer trading strategi
- **trader.py** - Placerer handler via Firi API
- **firebase_store.py** - Gemmer alle data i Firebase Firestore
- **main.py** - Kører loop, logging og orchestrering
- **models.py** - Data modeller (dataclasses)

## Strategi

- **KØB**: Når medium EMA går over long EMA og holder sig der i 3 candles i træk
- **SÆLG**: Når short EMA går under medium EMA og holder sig der i 3 candles i træk
- **Pair**: BTC/DKK (konfigurerbart via `TRADING_PAIR`)
- **Indikatorer**: 
  - Short EMA: 10 perioder (konfigurerbart via `SHORT_EMA_PERIOD`)
  - Medium EMA: 20 perioder (konfigurerbart via `MEDIUM_EMA_PERIOD`)
  - Long EMA: 50 perioder (konfigurerbart via `LONG_EMA_PERIOD`)
- **Max ét åbent trade af gangen**
- **Trailing Stop-Loss**: 7% (konfigurerbart via `TRAILING_STOP_LOSS_PERCENT`)
- **Cooldown**: 25 candles efter et sell før nyt køb tillades (konfigurerbart via `COOLDOWN_CANDLES`)

## Installation

1. Klon eller download projektet

2. Installer dependencies:
```bash
pip install -r requirements.txt
```

3. Opret Firebase projekt:
   - Gå til [Firebase Console](https://console.firebase.google.com/)
   - Opret nyt projekt
   - Aktiver Firestore Database
   - Gå til Project Settings > Service Accounts
   - Generer ny private key og download JSON-filen

4. Konfigurer environment variabler:
   - Kopier `.env.example` til `.env`
   - Udfyld alle værdier:
     - `FIRI_API_KEY`: Din Firi API nøgle
     - `FIRI_SECRET`: Din Firi API secret
     - `GOOGLE_APPLICATION_CREDENTIALS`: Sti til Firebase service account JSON-fil
     - Juster andre indstillinger efter behov

## Kørsel

```bash
python main.py
```

Botten kører kontinuerligt og:
- Henter prisdata hver 5. minut (konfigurerbart via `POLL_INTERVAL`)
- Genererer trading signals baseret på strategien
- Placerer handler automatisk
- Gemmer alle data i Firebase Firestore
- Logger alle aktiviteter til `trading_bot.log`

## Testing

Kør alle tests:

```bash
pytest
```

### Pre-push hook (tests før push)

Projektet er konfigureret til at køre tests automatisk før hver `git push`. Hvis tests fejler, bliver push blokeret.

Hooks er allerede konfigureret via `git config core.hooksPath .githooks`. Hvis du kloner projektet, kør:

```bash
# Windows (PowerShell)
.\scripts\setup-hooks.ps1

# Linux/macOS
./scripts/setup-hooks.sh
```

## Firebase Struktur

Botten gemmer data i følgende Firestore collections:

- **trades/{tradeId}** - Alle handler
- **signals/{timestamp}** - Trading signals
- **portfolio/current** - Nuværende portfolio state
- **portfolio/history/snapshots/{timestamp}** - Historiske portfolio snapshots
- **prices/{timestamp}** - Pris snapshots

## Deployment på VPS

### 1. Forbered VPS

```bash
# Opdater system
sudo apt update && sudo apt upgrade -y

# Installer Python og pip
sudo apt install python3 python3-pip python3-venv -y

# Installer git hvis nødvendigt
sudo apt install git -y
```

### 2. Upload projektet

```bash
# Klon projektet eller upload filer
cd /opt
sudo mkdir trading-bot
sudo chown $USER:$USER trading-bot
cd trading-bot

# Upload alle filer hertil (via scp, rsync, eller git clone)
```

### 3. Opsæt Python miljø

```bash
# Opret virtual environment
python3 -m venv venv
source venv/bin/activate

# Installer dependencies
pip install -r requirements.txt
```

### 4. Konfigurer environment

```bash
# Opret .env fil
nano .env

# Indsæt alle nødvendige variabler (se .env.example)
# Upload Firebase service account JSON til VPS
# Opdater GOOGLE_APPLICATION_CREDENTIALS sti
```

### 5. Opret systemd service

Opret `/etc/systemd/system/trading-bot.service`:

```ini
[Unit]
Description=Firi Trading Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/trading-bot
Environment="PATH=/opt/trading-bot/venv/bin"
ExecStart=/opt/trading-bot/venv/bin/python /opt/trading-bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Aktiver og start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo systemctl status trading-bot
```

### 6. Se logs

```bash
# Systemd logs
sudo journalctl -u trading-bot -f

# Eller app logs
tail -f /opt/trading-bot/trading_bot.log
```

## Integration med Web Frontend

### Firebase Firestore Integration

Din web frontend kan læse data direkte fra Firestore:

```javascript
// Eksempel med Firebase JS SDK
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, query, orderBy, limit, onSnapshot } from 'firebase/firestore';

const firebaseConfig = {
  // Din Firebase config
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

// Lyt til real-time updates af trades
const tradesRef = collection(db, 'trades');
const q = query(tradesRef, orderBy('timestamp', 'desc'), limit(10));
onSnapshot(q, (snapshot) => {
  snapshot.forEach((doc) => {
    console.log('Trade:', doc.data());
  });
});

// Hent portfolio state
const portfolioRef = doc(db, 'portfolio', 'current');
onSnapshot(portfolioRef, (doc) => {
  console.log('Portfolio:', doc.data());
});
```

### REST API (Valgfri)

Hvis du vil have en REST API, kan du oprette en separat Flask/FastAPI service der læser fra Firestore:

```python
# api_server.py (eksempel)
from flask import Flask, jsonify
from firebase_store import FirebaseStore

app = Flask(__name__)
firebase = FirebaseStore()

@app.route('/api/trades')
def get_trades():
    trades = firebase.get_all_trades(limit=100)
    return jsonify([t.to_dict() for t in trades])

@app.route('/api/portfolio')
def get_portfolio():
    portfolio = firebase.get_current_portfolio_state()
    return jsonify(portfolio.to_dict() if portfolio else {})
```

## Firebase Security Rules

Deploy Firebase security rules:

```bash
# Installer Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialiser projekt (hvis ikke allerede gjort)
firebase init firestore

# Deploy rules
firebase deploy --only firestore:rules
```

Eller upload `firestore.rules` manuelt via Firebase Console.

## Sikkerhed

- **ALDRIG** commit `.env` filen til git
- Brug `.gitignore` til at ekskludere:
  - `.env`
  - `*.json` (service account keys)
  - `venv/`
  - `__pycache__/`
  - `*.log`

## Troubleshooting

### Bot stopper med fejl
- Tjek logs: `tail -f trading_bot.log`
- Verificer API credentials i `.env`
- Tjek Firebase service account permissions

### Ingen handler placeres
- Verificer at der er tilstrækkelig balance
- Tjek at strategi betingelser er opfyldt
- Se signal logs i Firebase

### Firebase connection fejl
- Verificer `GOOGLE_APPLICATION_CREDENTIALS` sti
- Tjek at service account JSON er gyldig
- Verificer Firestore er aktiveret i Firebase projekt

## Licens

Dette projekt er til brug som reference. Brug på eget ansvar.

