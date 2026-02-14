# Deployment Guide - Firi Trading Bot

## Komplet Deployment Guide til VPS

### Forudsætninger

- VPS med Ubuntu 20.04+ eller lignende Linux distribution
- Root eller sudo adgang
- Firi API credentials
- Firebase projekt oprettet

---

## Trin 1: VPS Opsætning

### 1.1 Opdater systemet

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.2 Installer nødvendige pakker

```bash
sudo apt install -y python3 python3-pip python3-venv git curl
```

### 1.3 Opret bruger til bot (anbefalet)

```bash
sudo adduser tradingbot
sudo usermod -aG sudo tradingbot
su - tradingbot
```

---

## Trin 2: Upload Projektet

### 2.1 Via Git (anbefalet)

```bash
cd /home/tradingbot
git clone <dit-repo-url> trading-bot
cd trading-bot
```

### 2.2 Via SCP (alternativ)

Fra din lokale maskine:

```bash
scp -r /path/to/BotAgain tradingbot@your-vps-ip:/home/tradingbot/trading-bot
```

---

## Trin 3: Python Miljø Opsætning

### 3.1 Opret virtual environment

```bash
cd /home/tradingbot/trading-bot
python3 -m venv venv
source venv/bin/activate
```

### 3.2 Installer dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Trin 4: Firebase Konfiguration

### 4.1 Download Service Account Key

1. Gå til [Firebase Console](https://console.firebase.google.com/)
2. Vælg dit projekt
3. Gå til Project Settings > Service Accounts
4. Klik "Generate new private key"
5. Download JSON filen

### 4.2 Upload til VPS

```bash
# Fra din lokale maskine
scp service-account-key.json tradingbot@your-vps-ip:/home/tradingbot/trading-bot/
```

### 4.3 Sæt korrekte permissions

```bash
chmod 600 /home/tradingbot/trading-bot/service-account-key.json
```

---

## Trin 5: Environment Konfiguration

### 5.1 Opret .env fil

```bash
cd /home/tradingbot/trading-bot
nano .env
```

### 5.2 Indsæt følgende (opdater med dine værdier):

```env
FIRI_API_KEY=din_firi_api_key
FIRI_SECRET=din_firi_secret
FIRI_BASE_URL=https://api.firi.com

GOOGLE_APPLICATION_CREDENTIALS=/home/tradingbot/trading-bot/service-account-key.json

TRADING_PAIR=BTC/NOK
SHORT_EMA_PERIOD=12
LONG_EMA_PERIOD=26
TAKE_PROFIT_PERCENT=5.0
STOP_LOSS_PERCENT=3.0
CANDLE_INTERVAL=1h
POLL_INTERVAL=300
```

### 5.3 Gem og luk

```bash
# Ctrl+X, Y, Enter
chmod 600 .env
```

---

## Trin 6: Test Kørsel

### 6.1 Test at alt virker

```bash
source venv/bin/activate
python main.py
```

Lad det køre i 1-2 minutter og tjek logs. Stop med Ctrl+C.

---

## Trin 7: Systemd Service Opsætning

### 7.1 Opret service fil

```bash
sudo nano /etc/systemd/system/trading-bot.service
```

### 7.2 Indsæt følgende (opdater stier hvis nødvendigt):

```ini
[Unit]
Description=Firi Trading Bot
After=network.target

[Service]
Type=simple
User=tradingbot
Group=tradingbot
WorkingDirectory=/home/tradingbot/trading-bot
Environment="PATH=/home/tradingbot/trading-bot/venv/bin"
ExecStart=/home/tradingbot/trading-bot/venv/bin/python /home/tradingbot/trading-bot/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 7.3 Aktiver og start service

```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

### 7.4 Tjek status

```bash
sudo systemctl status trading-bot
```

---

## Trin 8: Logging og Monitoring

### 8.1 Se live logs

```bash
# Systemd logs
sudo journalctl -u trading-bot -f

# App logs
tail -f /home/tradingbot/trading-bot/trading_bot.log
```

### 8.2 Opret log rotation

```bash
sudo nano /etc/logrotate.d/trading-bot
```

Indsæt:

```
/home/tradingbot/trading-bot/trading_bot.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 tradingbot tradingbot
}
```

---

## Trin 9: Firebase Security Rules

### 9.1 Installer Firebase CLI

```bash
curl -sL https://firebase.tools | bash
```

### 9.2 Login til Firebase

```bash
firebase login
```

### 9.3 Initialiser Firestore (hvis ikke allerede gjort)

```bash
cd /home/tradingbot/trading-bot
firebase init firestore
```

Vælg dit projekt og accepter standard indstillinger.

### 9.4 Deploy security rules

```bash
firebase deploy --only firestore:rules
```

---

## Trin 10: Web Frontend Integration

### 10.1 Firebase Web SDK Setup

I din web frontend, tilføj Firebase config:

```javascript
// firebase-config.js
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id"
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
```

### 10.2 Læs Data fra Firestore

```javascript
// trades.js
import { db } from './firebase-config';
import { collection, query, orderBy, limit, onSnapshot } from 'firebase/firestore';

// Real-time trades
export function subscribeToTrades(callback) {
  const q = query(
    collection(db, 'trades'),
    orderBy('timestamp', 'desc'),
    limit(50)
  );
  
  return onSnapshot(q, (snapshot) => {
    const trades = snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    }));
    callback(trades);
  });
}

// Portfolio state
export function subscribeToPortfolio(callback) {
  const portfolioRef = doc(db, 'portfolio', 'current');
  return onSnapshot(portfolioRef, (doc) => {
    callback(doc.data());
  });
}
```

### 10.3 React Eksempel

```jsx
// TradingDashboard.jsx
import { useEffect, useState } from 'react';
import { subscribeToTrades, subscribeToPortfolio } from './trades';

function TradingDashboard() {
  const [trades, setTrades] = useState([]);
  const [portfolio, setPortfolio] = useState(null);

  useEffect(() => {
    const unsubscribeTrades = subscribeToTrades(setTrades);
    const unsubscribePortfolio = subscribeToPortfolio(setPortfolio);
    
    return () => {
      unsubscribeTrades();
      unsubscribePortfolio();
    };
  }, []);

  return (
    <div>
      <h1>Portfolio: {portfolio?.total_value_nok?.toFixed(2)} NOK</h1>
      <h2>Trades ({trades.length})</h2>
      <ul>
        {trades.map(trade => (
          <li key={trade.id}>
            {trade.side} {trade.quantity} @ {trade.price} NOK
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Vedligeholdelse

### Opdater bot

```bash
cd /home/tradingbot/trading-bot
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart trading-bot
```

### Se status

```bash
sudo systemctl status trading-bot
```

### Stop/Start

```bash
sudo systemctl stop trading-bot
sudo systemctl start trading-bot
sudo systemctl restart trading-bot
```

### Fjern service

```bash
sudo systemctl stop trading-bot
sudo systemctl disable trading-bot
sudo rm /etc/systemd/system/trading-bot.service
sudo systemctl daemon-reload
```

---

## Troubleshooting

### Service fejler at starte

```bash
# Tjek logs
sudo journalctl -u trading-bot -n 50

# Tjek permissions
ls -la /home/tradingbot/trading-bot/
```

### Firebase connection fejl

```bash
# Verificer service account key
cat /home/tradingbot/trading-bot/service-account-key.json | head -5

# Test Firebase connection
python3 -c "from firebase_store import FirebaseStore; fs = FirebaseStore(); print('OK')"
```

### API fejl

```bash
# Test Firi API connection
python3 -c "from data_fetcher import FiriDataFetcher; df = FiriDataFetcher(); print(df.get_latest_price('BTC/NOK'))"
```

---

## Sikkerhedsbestemmelser

1. **Firewall**: Sæt op firewall (UFW)
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw enable
   ```

2. **SSH Keys**: Brug SSH keys i stedet for passwords

3. **Backup**: Opret regelmæssige backups af:
   - `.env` fil
   - Service account key
   - Firebase data (via Firebase Console)

4. **Monitoring**: Overvej at sætte op monitoring (f.eks. Sentry, DataDog)

---

## Support

Ved problemer, tjek:
1. Logs: `sudo journalctl -u trading-bot -f`
2. App logs: `tail -f trading_bot.log`
3. Firebase Console for data
4. Firi API dokumentation

