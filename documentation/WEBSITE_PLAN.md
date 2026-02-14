# Plan: Trading Bot Dashboard Website

## Oversigt
Et simpelt, responsivt website der viser trading bot data fra Firebase Firestore. Websitet er read-only og viser kun data - ingen trading funktionalitet.

---

## 1. Teknisk Stack

### Frontend
- **HTML5** - Struktur
- **CSS3** - Styling (med moderne CSS Grid/Flexbox)
- **Vanilla JavaScript (ES6+)** - Ingen frameworks for at holde det simpelt
- **Chart.js** - For visualiseringer (letvægt, god dokumentation)
- **Firebase SDK (v9+)** - Til at hente data fra Firestore

### Hosting
- **Firebase Hosting** - Gratis, integreret med Firebase projektet
- Alternativ: **Netlify**, **Vercel**, eller **GitHub Pages**

---

## 2. Firebase Data Struktur

### Collections der skal bruges:
1. **`prices/`** - Price snapshots (Candle data)
   - `timestamp`: ISO datetime string
   - `open`, `high`, `low`, `close`: float
   - `volume`: float
   - `pair`: string (f.eks. "BTC/DKK")

2. **`signals/`** - Trading signals
   - `timestamp`: ISO datetime string
   - `price`: float
   - `short_ema`: float (10-perioder EMA)
   - `long_ema`: float (kan være medium eller long EMA afhængigt af signal)
   - `signal_type`: "buy", "sell", "hold"
   - `reason`: string

3. **`trades/`** - Trades (optional, kan vises senere)
4. **`portfolio/current`** - Portfolio state (optional, kan vises senere)

### Bemærkning om EMA data:
- `signals` collection har `short_ema` og `long_ema`, men ikke `medium_ema` direkte
- For at få alle tre EMA værdier (short, medium, long), skal vi:
  - Hente seneste signal (har short_ema og long_ema)
  - Beregne medium_ema fra price snapshots, ELLER
  - Opdatere Signal modellen til at gemme alle tre EMA værdier

---

## 3. Filstruktur

```
web/
├── index.html              # Hovedside
├── css/
│   └── styles.css         # Styling
├── js/
│   ├── firebase-config.js  # Firebase konfiguration
│   ├── data-fetcher.js     # Henter data fra Firestore
│   ├── chart-renderer.js   # Chart.js visualiseringer
│   └── ui-updater.js        # Opdaterer UI med data
├── assets/
│   └── (logo, icons, etc.)
└── README.md               # Deployment instruktioner
```

---

## 4. Features & Sider

### Hovedside (`index.html`)

#### Sektion 1: Seneste Priser (Liste)
- **Tabel visning** med:
  - Timestamp
  - Åben (Open)
  - Høj (High)
  - Lav (Low)
  - Luk (Close)
  - Volumen
  - Kort EMA (10)
  - Mellem EMA (20)
  - Lang EMA (50)

#### Sektion 2: Pris Visualisering
- **Chart.js Line Chart** eller **Candlestick Chart**
- Viser:
  - Close price (blå linje)
  - Short EMA (10) - orange linje
  - Medium EMA (20) - lilla linje
  - Long EMA (50) - brun linje
- X-akse: Tid
- Y-akse: Pris (DKK)
- Tidsperiode selector: 1h, 4h, 1d, 7d, 30d

#### Sektion 3: EMA Værdier (Liste)
- **Kort oversigt** med seneste EMA værdier:
  - Short EMA: [værdi] DKK
  - Medium EMA: [værdi] DKK
  - Long EMA: [værdi] DKK
  - Opdateret: [timestamp]

#### Sektion 4: Seneste Signals (Optional)
- Liste af seneste trading signals
- Viser signal type (BUY/SELL/HOLD) med farvekodning

---

## 5. Firebase Konfiguration

### `firebase-config.js`
```javascript
const firebaseConfig = {
  apiKey: "AIzaSyBP8j5g9of_a7xachnOmhqVQ5jSDUseMD4",
  authDomain: "anothertraderbot.firebaseapp.com",
  projectId: "anothertraderbot",
  storageBucket: "anothertraderbot.firebasestorage.app",
  messagingSenderId: "111756188492",
  appId: "1:111756188492:web:861d758c4de689a6d4cde9",
  measurementId: "G-TJ55RJ7C65"
};
```

### Firestore Security Rules
For at websitet kan læse data, skal Firestore rules opdateres:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow public read access to prices
    match /prices/{priceId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
    
    // Allow public read access to signals
    match /signals/{signalId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
    
    // Keep trades and portfolio private
    match /trades/{tradeId} {
      allow read, write: if request.auth != null;
    }
    
    match /portfolio/{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

---

## 6. Data Hentning Logik

### `data-fetcher.js` Funktioner:

1. **`getLatestPrices(limit = 100)`**
   - Henter seneste price snapshots fra `prices/` collection
   - Sorterer efter timestamp (descending)
   - Returnerer array af candle objekter

2. **`getLatestSignals(limit = 50)`**
   - Henter seneste signals fra `signals/` collection
   - Sorterer efter timestamp (descending)
   - Returnerer array af signal objekter

3. **`getLatestEMAValues()`**
   - Henter seneste signal (har short_ema og long_ema)
   - Beregner medium_ema fra price snapshots hvis ikke tilgængelig
   - Returnerer objekt med {short_ema, medium_ema, long_ema}

4. **`calculateEMAFromPrices(prices, period)`**
   - Beregner EMA fra price snapshots
   - Brug til at beregne medium_ema hvis ikke i signals

---

## 7. Visualiseringer

### Chart.js Setup:

**Pris Chart:**
- Type: Line chart eller Candlestick chart
- Datasets:
  - Close Price (blå, solid)
  - Short EMA (orange, dashed)
  - Medium EMA (lilla, dashed)
  - Long EMA (brun, dashed)
- Responsive design
- Zoom/pan funktionalitet (Chart.js zoom plugin)

**EMA Comparison Chart (Optional):**
- Bar chart eller line chart
- Sammenligner de tre EMA værdier over tid

---

## 8. UI/UX Design

### Design Principper:
- **Moderne og rent** - Minimalistisk design
- **Responsivt** - Fungerer på desktop, tablet og mobil
- **Mørkt tema** (optional) - Godt for trading dashboards
- **Real-time opdatering** - Opdaterer automatisk hver 30-60 sekunder

### Farver:
- Primary: Blå (#3B82F6)
- Success: Grøn (#10B981) - for BUY signals
- Danger: Rød (#EF4444) - for SELL signals
- Warning: Orange (#F59E0B) - for HOLD signals
- Background: Hvid/Lys grå eller Mørk (#1F2937)

### Typografi:
- Headers: Sans-serif (f.eks. Inter, Roboto)
- Body: Sans-serif
- Monospace for tal/priser

---

## 9. Real-time Opdatering

### Strategi:
1. **Polling** - Hent data hver 30-60 sekunder
2. **Firestore Listeners** (optional) - Real-time updates når data ændres
3. **Manual Refresh** - Knap til at opdatere manuelt

### Implementering:
```javascript
// Polling approach
setInterval(async () => {
  await updateAllData();
}, 60000); // Update every 60 seconds
```

---

## 10. Deployment

### Firebase Hosting:

1. **Install Firebase CLI:**
   ```bash
   npm install -g firebase-tools
   ```

2. **Login:**
   ```bash
   firebase login
   ```

3. **Initialize hosting:**
   ```bash
   firebase init hosting
   ```
   - Select existing project: `anothertraderbot`
   - Public directory: `web`
   - Single-page app: No
   - GitHub auto-deploy: Optional

4. **Deploy:**
   ```bash
   firebase deploy --only hosting
   ```

5. **URL:**
   - `https://anothertraderbot.web.app`
   - `https://anothertraderbot.firebaseapp.com`

### Alternativ: Netlify/Vercel
- Drag & drop `web/` folder
- Eller connect GitHub repo og auto-deploy

---

## 11. Implementerings Faser

### Fase 1: Basis Setup (1-2 timer)
- [ ] Opret filstruktur
- [ ] Firebase konfiguration
- [ ] Basis HTML struktur
- [ ] CSS styling

### Fase 2: Data Hentning (2-3 timer)
- [ ] Implementer `data-fetcher.js`
- [ ] Test Firebase forbindelse
- [ ] Hent prices og signals

### Fase 3: Liste Visning (1-2 timer)
- [ ] Implementer pris tabel
- [ ] Implementer EMA værdier liste
- [ ] Opdater UI med data

### Fase 4: Visualisering (2-3 timer)
- [ ] Setup Chart.js
- [ ] Implementer pris chart
- [ ] Tilføj EMA linjer
- [ ] Responsive design

### Fase 5: Real-time & Polish (1-2 timer)
- [ ] Implementer auto-refresh
- [ ] Fejlhåndtering
- [ ] Loading states
- [ ] Final styling

**Total estimeret tid: 7-12 timer**

---

## 12. Forbedringer (Fremtidige Features)

- [ ] Historisk data visning (7d, 30d, 90d)
- [ ] Trades visning
- [ ] Portfolio performance
- [ ] Signal historik med filtre
- [ ] Export data til CSV
- [ ] Mørkt/lyst tema toggle
- [ ] Notifikationer ved nye signals
- [ ] Mobile app (PWA)

---

## 13. Vigtige Overvejelser

### Sikkerhed:
- Firestore rules skal tillade public read for `prices/` og `signals/`
- Ingen API keys eller secrets i frontend kode
- Rate limiting kan være nødvendigt hvis der er mange requests

### Performance:
- Begræns antal documents der hentes (f.eks. max 100-200)
- Cache data lokalt hvis muligt
- Lazy loading af charts

### Data Konsistens:
- Signal modellen skal muligvis opdateres til at gemme alle tre EMA værdier
- Ellers skal medium_ema beregnes fra price snapshots

---

## 14. Næste Skridt

1. **Opdater Signal model** (hvis nødvendigt) til at gemme `medium_ema`
2. **Opdater Firestore rules** til at tillade public read
3. **Opret web/ mappe** og filstruktur
4. **Implementer Firebase konfiguration**
5. **Byg UI komponenter** én ad gangen
6. **Test lokalt** først
7. **Deploy til Firebase Hosting**

---

## 15. Ressourcer

- Firebase Documentation: https://firebase.google.com/docs
- Chart.js Documentation: https://www.chartjs.org/docs/
- Firestore Queries: https://firebase.google.com/docs/firestore/query-data/queries
- Firebase Hosting: https://firebase.google.com/docs/hosting

---

**Status:** Plan klar - klar til implementering 🚀









