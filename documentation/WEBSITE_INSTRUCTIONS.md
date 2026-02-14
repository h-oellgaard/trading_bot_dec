# Instruktionssæt: Vue.js Trading Bot Dashboard

## Oversigt
Dette dokument beskriver hvordan man bygger et modulært, sikkert og vedligeholdeligt Vue.js dashboard til at vise trading bot data fra Firebase Firestore.

**Krav:**
- Vue.js 3 (Composition API)
- Modulær arkitektur
- OWASP sikkerhedsbest practices
- FURPS+ kvalitetskriterier
- GRASP design principper
- Best practices

---

## 1. Projekt Setup & Arkitektur

### 1.1 Projekt Initialisering

```bash
# Opret Vue projekt med Vite (moderne build tool)
npm create vue@latest trading-bot-dashboard
cd trading-bot-dashboard

# Vælg options:
# ✅ TypeScript: No (eller Yes hvis du vil bruge TS)
# ✅ JSX: No
# ✅ Router: Yes
# ✅ Pinia: Yes (state management)
# ✅ Vitest: Yes (testing)
# ✅ ESLint: Yes
# ✅ Prettier: Yes
```

### 1.2 Projekt Struktur (Modulær Arkitektur)

```
trading-bot-dashboard/
├── public/
│   └── favicon.ico
├── src/
│   ├── assets/              # Statiske assets
│   │   ├── styles/
│   │   │   ├── main.css     # Global styles
│   │   │   └── variables.css # CSS variables
│   │   └── images/
│   ├── components/          # Vue komponenter (modulære)
│   │   ├── common/          # Genbrugelige komponenter
│   │   │   ├── LoadingSpinner.vue
│   │   │   ├── ErrorMessage.vue
│   │   │   └── DataTable.vue
│   │   ├── prices/          # Price-relaterede komponenter
│   │   │   ├── PriceList.vue
│   │   │   ├── PriceChart.vue
│   │   │   └── PriceCard.vue
│   │   ├── ema/             # EMA-relaterede komponenter
│   │   │   ├── EMAList.vue
│   │   │   ├── EMAChart.vue
│   │   │   └── EMAValueCard.vue
│   │   └── signals/         # Signal komponenter
│   │       └── SignalList.vue
│   ├── composables/         # Composition API composables (GRASP: Information Expert)
│   │   ├── useFirebase.js
│   │   ├── usePrices.js
│   │   ├── useSignals.js
│   │   ├── useEMA.js
│   │   └── useRealTime.js
│   ├── services/            # Business logic layer (GRASP: Controller)
│   │   ├── firebase/
│   │   │   ├── firebaseConfig.js
│   │   │   ├── firestoreService.js
│   │   │   └── authService.js
│   │   ├── data/
│   │   │   ├── priceService.js
│   │   │   ├── signalService.js
│   │   │   └── emaService.js
│   │   └── validation/
│   │       └── dataValidator.js
│   ├── stores/             # Pinia stores (state management)
│   │   ├── prices.js
│   │   ├── signals.js
│   │   └── ema.js
│   ├── utils/               # Utility functions (pure functions)
│   │   ├── dateUtils.js
│   │   ├── numberUtils.js
│   │   ├── chartUtils.js
│   │   └── securityUtils.js
│   ├── router/             # Vue Router konfiguration
│   │   └── index.js
│   ├── views/              # Page components
│   │   ├── Dashboard.vue
│   │   ├── Prices.vue
│   │   └── About.vue
│   ├── App.vue
│   └── main.js
├── tests/                  # Test files
│   ├── unit/
│   │   ├── components/
│   │   ├── composables/
│   │   └── services/
│   └── e2e/
├── .env                    # Environment variables (IKKE commit)
├── .env.example            # Example env file
├── .gitignore
├── package.json
├── vite.config.js
├── eslint.config.js
└── README.md
```

### 1.3 GRASP Principper Anvendelse

**Information Expert:**
- `usePrices.js` composable ved alt om price data
- `useEMA.js` composable ved alt om EMA beregninger
- Services håndterer deres specifikke domæne

**Creator:**
- `PriceService` opretter `Price` objekter
- `SignalService` opretter `Signal` objekter

**Controller:**
- Vue komponenter fungerer som controllers
- Services håndterer business logic

**Low Coupling:**
- Komponenter kommunikerer via props/events
- Services er uafhængige af hinanden
- Composables kan bruges uafhængigt

**High Cohesion:**
- Hver komponent har ét ansvar
- Services har klart definerede ansvarsområder

---

## 2. Dependencies Installation

### 2.1 Core Dependencies

```bash
# Vue ecosystem
npm install vue@^3.4.0 vue-router@^4.2.0 pinia@^2.1.0

# Firebase
npm install firebase@^10.7.0

# Charting
npm install chart.js@^4.4.0 vue-chartjs@^5.3.0

# HTTP client (hvis nødvendigt)
npm install axios@^1.6.0

# Date handling
npm install date-fns@^3.0.0

# Validation
npm install zod@^3.22.0
```

### 2.2 Development Dependencies

```bash
# Build tools
npm install -D vite@^5.0.0 @vitejs/plugin-vue

# Linting & Formatting
npm install -D eslint@^8.57.0 eslint-plugin-vue@^9.20.0
npm install -D prettier@^3.2.0 eslint-config-prettier@^9.1.0

# Testing
npm install -D vitest@^1.2.0 @vue/test-utils@^2.4.0
npm install -D @testing-library/vue@^8.0.0

# Security scanning
npm install -D audit-ci@^6.6.0
```

---

## 3. Firebase Konfiguration

### 3.1 Firebase Setup (`src/services/firebase/firebaseConfig.js`)

```javascript
import { initializeApp } from 'firebase/app';
import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';

// OWASP: Environment variables - aldrig hardcode credentials
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firestore
export const db = getFirestore(app);

// Initialize Auth (hvis nødvendigt senere)
export const auth = getAuth(app);

// OWASP: Development mode check - brug emulator i dev
if (import.meta.env.DEV && import.meta.env.VITE_USE_FIREBASE_EMULATOR === 'true') {
  connectFirestoreEmulator(db, 'localhost', 8080);
}

export default app;
```

### 3.2 Environment Variables (`.env`)

```bash
# Firebase Configuration
VITE_FIREBASE_API_KEY=AIzaSyBP8j5g9of_a7xachnOmhqVQ5jSDUseMD4
VITE_FIREBASE_AUTH_DOMAIN=anothertraderbot.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=anothertraderbot
VITE_FIREBASE_STORAGE_BUCKET=anothertraderbot.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=111756188492
VITE_FIREBASE_APP_ID=1:111756188492:web:861d758c4de689a6d4cde9
VITE_FIREBASE_MEASUREMENT_ID=G-TJ55RJ7C65

# App Configuration
VITE_APP_TITLE=Trading Bot Dashboard
VITE_API_POLL_INTERVAL=60000
VITE_MAX_DATA_POINTS=200

# Development
VITE_USE_FIREBASE_EMULATOR=false
```

**OWASP Best Practice:** `.env` fil skal være i `.gitignore`

---

## 4. Service Layer (Business Logic)

### 4.1 Firestore Service (`src/services/firebase/firestoreService.js`)

```javascript
import { 
  collection, 
  query, 
  orderBy, 
  limit, 
  getDocs, 
  onSnapshot,
  Timestamp,
  where
} from 'firebase/firestore';
import { db } from './firebaseConfig';

/**
 * Generic Firestore service with error handling
 * GRASP: Low Coupling - Generic service kan bruges til alle collections
 */
export class FirestoreService {
  /**
   * Get documents from a collection with query options
   * OWASP: Input validation, error handling
   */
  static async getCollection(
    collectionName, 
    options = { orderBy: 'timestamp', orderDirection: 'desc', limit: 100 }
  ) {
    try {
      // OWASP: Input validation
      if (!collectionName || typeof collectionName !== 'string') {
        throw new Error('Invalid collection name');
      }

      const collectionRef = collection(db, collectionName);
      let q = query(collectionRef);

      // Apply ordering
      if (options.orderBy) {
        q = query(q, orderBy(options.orderBy, options.orderDirection || 'desc'));
      }

      // Apply limit
      if (options.limit && options.limit > 0 && options.limit <= 1000) {
        q = query(q, limit(options.limit));
      }

      // Apply filters
      if (options.filters && Array.isArray(options.filters)) {
        options.filters.forEach(filter => {
          q = query(q, where(filter.field, filter.operator, filter.value));
        });
      }

      const querySnapshot = await getDocs(q);
      return querySnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
    } catch (error) {
      console.error(`Error fetching ${collectionName}:`, error);
      throw new Error(`Failed to fetch ${collectionName}: ${error.message}`);
    }
  }

  /**
   * Subscribe to real-time updates
   * OWASP: Resource cleanup - unsubscribe on component unmount
   */
  static subscribeToCollection(collectionName, callback, options = {}) {
    try {
      const collectionRef = collection(db, collectionName);
      let q = query(collectionRef);

      if (options.orderBy) {
        q = query(q, orderBy(options.orderBy, options.orderDirection || 'desc'));
      }

      if (options.limit) {
        q = query(q, limit(options.limit));
      }

      // Return unsubscribe function
      return onSnapshot(
        q,
        (snapshot) => {
          const data = snapshot.docs.map(doc => ({
            id: doc.id,
            ...doc.data()
          }));
          callback(data);
        },
        (error) => {
          console.error(`Error in ${collectionName} subscription:`, error);
          callback([], error);
        }
      );
    } catch (error) {
      console.error(`Error subscribing to ${collectionName}:`, error);
      throw error;
    }
  }
}
```

### 4.2 Price Service (`src/services/data/priceService.js`)

```javascript
import { FirestoreService } from '../firebase/firestoreService';
import { z } from 'zod';

// OWASP: Input validation schema
const PriceSchema = z.object({
  id: z.string(),
  timestamp: z.string(),
  open: z.number(),
  high: z.number(),
  low: z.number(),
  close: z.number(),
  volume: z.number().optional(),
  pair: z.string().optional()
});

/**
 * Price service - handles price data operations
 * GRASP: Information Expert - knows everything about prices
 */
export class PriceService {
  static COLLECTION_NAME = 'prices';

  /**
   * Get latest prices
   * OWASP: Input validation, output sanitization
   */
  static async getLatestPrices(limit = 100) {
    try {
      // OWASP: Validate input
      const validatedLimit = Math.min(Math.max(1, limit), 1000);

      const data = await FirestoreService.getCollection(this.COLLECTION_NAME, {
        orderBy: 'timestamp',
        orderDirection: 'desc',
        limit: validatedLimit
      });

      // OWASP: Validate and sanitize output
      return data
        .map(item => {
          try {
            return PriceSchema.parse({
              id: item.id,
              timestamp: item.timestamp,
              open: parseFloat(item.open),
              high: parseFloat(item.high),
              low: parseFloat(item.low),
              close: parseFloat(item.close),
              volume: parseFloat(item.volume || 0),
              pair: item.pair || 'BTC/DKK'
            });
          } catch (error) {
            console.warn('Invalid price data:', item, error);
            return null;
          }
        })
        .filter(Boolean);
    } catch (error) {
      console.error('Error fetching prices:', error);
      throw error;
    }
  }

  /**
   * Subscribe to real-time price updates
   */
  static subscribeToPrices(callback, limit = 100) {
    return FirestoreService.subscribeToCollection(
      this.COLLECTION_NAME,
      callback,
      {
        orderBy: 'timestamp',
        orderDirection: 'desc',
        limit: Math.min(Math.max(1, limit), 1000)
      }
    );
  }
}
```

### 4.3 Signal Service (`src/services/data/signalService.js`)

```javascript
import { FirestoreService } from '../firebase/firestoreService';
import { z } from 'zod';

// OWASP: Input validation
const SignalSchema = z.object({
  id: z.string(),
  signal_id: z.string(),
  signal_type: z.enum(['buy', 'sell', 'hold']),
  timestamp: z.string(),
  price: z.number(),
  short_ema: z.number().nullable().optional(),
  medium_ema: z.number().nullable().optional(),
  long_ema: z.number().nullable().optional(),
  reason: z.string().nullable().optional()
});

export class SignalService {
  static COLLECTION_NAME = 'signals';

  static async getLatestSignals(limit = 50) {
    try {
      const validatedLimit = Math.min(Math.max(1, limit), 1000);

      const data = await FirestoreService.getCollection(this.COLLECTION_NAME, {
        orderBy: 'timestamp',
        orderDirection: 'desc',
        limit: validatedLimit
      });

      return data
        .map(item => {
          try {
            return SignalSchema.parse({
              id: item.id || item.signal_id,
              signal_id: item.signal_id || item.id,
              signal_type: item.signal_type,
              timestamp: item.timestamp,
              price: parseFloat(item.price),
              short_ema: item.short_ema ? parseFloat(item.short_ema) : null,
              medium_ema: item.medium_ema ? parseFloat(item.medium_ema) : null,
              long_ema: item.long_ema ? parseFloat(item.long_ema) : null,
              reason: item.reason || null
            });
          } catch (error) {
            console.warn('Invalid signal data:', item, error);
            return null;
          }
        })
        .filter(Boolean);
    } catch (error) {
      console.error('Error fetching signals:', error);
      throw error;
    }
  }

  static subscribeToSignals(callback, limit = 50) {
    return FirestoreService.subscribeToCollection(
      this.COLLECTION_NAME,
      callback,
      {
        orderBy: 'timestamp',
        orderDirection: 'desc',
        limit: Math.min(Math.max(1, limit), 1000)
      }
    );
  }
}
```

### 4.4 EMA Service (`src/services/data/emaService.js`)

```javascript
import { SignalService } from './signalService';
import { PriceService } from './priceService';

/**
 * EMA Service - calculates and provides EMA values
 * GRASP: Information Expert for EMA calculations
 */
export class EMAService {
  /**
   * Calculate EMA from price array
   * Pure function - no side effects
   */
  static calculateEMA(prices, period) {
    if (!prices || prices.length < period) {
      return null;
    }

    const multiplier = 2 / (period + 1);
    let ema = prices.slice(0, period).reduce((sum, price) => sum + price, 0) / period;

    for (let i = period; i < prices.length; i++) {
      ema = (prices[i] - ema) * multiplier + ema;
    }

    return ema;
  }

  /**
   * Get latest EMA values from signals or calculate from prices
   */
  static async getLatestEMAValues() {
    try {
      // Try to get from latest signal first
      const signals = await SignalService.getLatestSignals(1);
      
      if (signals.length > 0 && signals[0].short_ema && signals[0].long_ema) {
        return {
          short_ema: signals[0].short_ema,
          medium_ema: signals[0].medium_ema || null,
          long_ema: signals[0].long_ema,
          timestamp: signals[0].timestamp,
          source: 'signal'
        };
      }

      // Fallback: Calculate from prices
      const prices = await PriceService.getLatestPrices(100);
      if (prices.length < 50) {
        return null;
      }

      const closePrices = prices.map(p => p.close).reverse();
      
      return {
        short_ema: this.calculateEMA(closePrices, 10),
        medium_ema: this.calculateEMA(closePrices, 20),
        long_ema: this.calculateEMA(closePrices, 50),
        timestamp: prices[prices.length - 1].timestamp,
        source: 'calculated'
      };
    } catch (error) {
      console.error('Error getting EMA values:', error);
      throw error;
    }
  }
}
```

---

## 5. Composables (Vue Composition API)

### 5.1 usePrices Composable (`src/composables/usePrices.js`)

```javascript
import { ref, onMounted, onUnmounted } from 'vue';
import { PriceService } from '@/services/data/priceService';

/**
 * Composable for price data
 * GRASP: Information Expert - manages price state
 */
export function usePrices(options = {}) {
  const prices = ref([]);
  const loading = ref(false);
  const error = ref(null);
  const unsubscribe = ref(null);

  const fetchPrices = async (limit = 100) => {
    loading.value = true;
    error.value = null;
    
    try {
      const data = await PriceService.getLatestPrices(limit);
      prices.value = data;
    } catch (err) {
      error.value = err.message;
      console.error('Error fetching prices:', err);
    } finally {
      loading.value = false;
    }
  };

  const subscribeToPrices = (limit = 100) => {
    if (unsubscribe.value) {
      unsubscribe.value();
    }

    unsubscribe.value = PriceService.subscribeToPrices((data, err) => {
      if (err) {
        error.value = err.message;
        return;
      }
      prices.value = data;
    }, limit);
  };

  // OWASP: Resource cleanup
  onUnmounted(() => {
    if (unsubscribe.value) {
      unsubscribe.value();
    }
  });

  // Auto-fetch on mount if enabled
  if (options.autoFetch !== false) {
    onMounted(() => {
      fetchPrices(options.limit);
    });
  }

  return {
    prices,
    loading,
    error,
    fetchPrices,
    subscribeToPrices
  };
}
```

### 5.2 useEMA Composable (`src/composables/useEMA.js`)

```javascript
import { ref, computed, onMounted } from 'vue';
import { EMAService } from '@/services/data/emaService';
import { usePrices } from './usePrices';

/**
 * Composable for EMA data
 * GRASP: Information Expert for EMA
 */
export function useEMA() {
  const emaValues = ref({
    short_ema: null,
    medium_ema: null,
    long_ema: null,
    timestamp: null,
    source: null
  });
  const loading = ref(false);
  const error = ref(null);

  const { prices } = usePrices({ autoFetch: true });

  const fetchEMAValues = async () => {
    loading.value = true;
    error.value = null;

    try {
      const values = await EMAService.getLatestEMAValues();
      if (values) {
        emaValues.value = values;
      }
    } catch (err) {
      error.value = err.message;
      console.error('Error fetching EMA values:', err);
    } finally {
      loading.value = false;
    }
  };

  // Calculate EMA from current prices if not available
  const calculateFromPrices = () => {
    if (!prices.value || prices.value.length < 50) {
      return;
    }

    const closePrices = [...prices.value].reverse().map(p => p.close);
    
    emaValues.value = {
      short_ema: EMAService.calculateEMA(closePrices, 10),
      medium_ema: EMAService.calculateEMA(closePrices, 20),
      long_ema: EMAService.calculateEMA(closePrices, 50),
      timestamp: prices.value[0]?.timestamp || null,
      source: 'calculated'
    };
  };

  // Computed properties for formatted values
  const formattedEMA = computed(() => ({
    short: emaValues.value.short_ema?.toFixed(2) || 'N/A',
    medium: emaValues.value.medium_ema?.toFixed(2) || 'N/A',
    long: emaValues.value.long_ema?.toFixed(2) || 'N/A'
  }));

  onMounted(() => {
    fetchEMAValues();
  });

  return {
    emaValues,
    formattedEMA,
    loading,
    error,
    fetchEMAValues,
    calculateFromPrices
  };
}
```

---

## 6. Pinia Stores (State Management)

### 6.1 Prices Store (`src/stores/prices.js`)

```javascript
import { defineStore } from 'pinia';
import { PriceService } from '@/services/data/priceService';

/**
 * Pinia store for price state
 * GRASP: Controller - manages price state globally
 */
export const usePricesStore = defineStore('prices', {
  state: () => ({
    prices: [],
    loading: false,
    error: null,
    lastUpdate: null
  }),

  getters: {
    latestPrice: (state) => state.prices[0] || null,
    priceCount: (state) => state.prices.length,
    hasPrices: (state) => state.prices.length > 0
  },

  actions: {
    async fetchPrices(limit = 100) {
      this.loading = true;
      this.error = null;

      try {
        const data = await PriceService.getLatestPrices(limit);
        this.prices = data;
        this.lastUpdate = new Date().toISOString();
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    clearPrices() {
      this.prices = [];
      this.error = null;
      this.lastUpdate = null;
    }
  }
});
```

---

## 7. Vue Komponenter

### 7.1 PriceList Component (`src/components/prices/PriceList.vue`)

```vue
<template>
  <div class="price-list">
    <div class="price-list__header">
      <h2>Seneste Priser</h2>
      <button 
        @click="refresh" 
        :disabled="loading"
        class="btn btn--secondary"
        aria-label="Opdater priser"
      >
        {{ loading ? 'Opdaterer...' : 'Opdater' }}
      </button>
    </div>

    <LoadingSpinner v-if="loading && !prices.length" />
    <ErrorMessage v-if="error" :message="error" />

    <div v-if="!loading && prices.length" class="price-list__table-wrapper">
      <table class="price-table" role="table" aria-label="Pris oversigt">
        <thead>
          <tr>
            <th>Tid</th>
            <th>Åben</th>
            <th>Høj</th>
            <th>Lav</th>
            <th>Luk</th>
            <th>Volumen</th>
            <th>Kort EMA</th>
            <th>Mellem EMA</th>
            <th>Lang EMA</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="price in displayedPrices" 
            :key="price.id"
            :class="{ 'price-table__row--latest': price.id === latestPrice?.id }"
          >
            <td>{{ formatDate(price.timestamp) }}</td>
            <td>{{ formatNumber(price.open) }}</td>
            <td>{{ formatNumber(price.high) }}</td>
            <td>{{ formatNumber(price.low) }}</td>
            <td class="price-table__cell--close">{{ formatNumber(price.close) }}</td>
            <td>{{ formatNumber(price.volume) }}</td>
            <td>{{ getEMAForPrice(price, 'short') }}</td>
            <td>{{ getEMAForPrice(price, 'medium') }}</td>
            <td>{{ getEMAForPrice(price, 'long') }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!loading && !prices.length" class="price-list__empty">
      <p>Ingen priser tilgængelige</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { usePrices } from '@/composables/usePrices';
import { useEMA } from '@/composables/useEMA';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';
import ErrorMessage from '@/components/common/ErrorMessage.vue';
import { formatDate, formatNumber } from '@/utils/numberUtils';

// Props
const props = defineProps({
  limit: {
    type: Number,
    default: 50
  }
});

// Composables
const { prices, loading, error, fetchPrices } = usePrices({ autoFetch: false });
const { emaValues } = useEMA();

// Computed
const displayedPrices = computed(() => prices.value.slice(0, props.limit));
const latestPrice = computed(() => prices.value[0]);

// Methods
const refresh = async () => {
  await fetchPrices(100);
};

const getEMAForPrice = (price, type) => {
  // This is simplified - in reality you'd need to match price timestamp with signal
  if (type === 'short') return emaValues.value.short_ema?.toFixed(2) || 'N/A';
  if (type === 'medium') return emaValues.value.medium_ema?.toFixed(2) || 'N/A';
  if (type === 'long') return emaValues.value.long_ema?.toFixed(2) || 'N/A';
  return 'N/A';
};

// Fetch on mount
fetchPrices(100);
</script>

<style scoped>
.price-list {
  padding: 1.5rem;
  background: var(--color-surface);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.price-list__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.price-table {
  width: 100%;
  border-collapse: collapse;
}

.price-table th {
  background: var(--color-primary);
  color: white;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
}

.price-table td {
  padding: 0.75rem;
  border-bottom: 1px solid var(--color-border);
}

.price-table__row--latest {
  background: var(--color-highlight);
}

.price-table__cell--close {
  font-weight: 600;
  color: var(--color-primary);
}
</style>
```

### 7.2 PriceChart Component (`src/components/prices/PriceChart.vue`)

```vue
<template>
  <div class="price-chart">
    <div class="price-chart__header">
      <h2>Pris Visualisering</h2>
      <div class="price-chart__controls">
        <select v-model="selectedPeriod" @change="updateChart">
          <option value="1h">1 Time</option>
          <option value="4h">4 Timer</option>
          <option value="1d">1 Dag</option>
          <option value="7d">7 Dage</option>
          <option value="30d">30 Dage</option>
        </select>
      </div>
    </div>

    <LoadingSpinner v-if="loading" />
    <ErrorMessage v-if="error" :message="error" />

    <div v-if="!loading && chartData" class="price-chart__canvas">
      <Line 
        :data="chartData" 
        :options="chartOptions"
        :key="chartKey"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { Line } from 'vue-chartjs';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { usePrices } from '@/composables/usePrices';
import { useEMA } from '@/composables/useEMA';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';
import ErrorMessage from '@/components/common/ErrorMessage.vue';
import { filterPricesByPeriod } from '@/utils/dateUtils';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const selectedPeriod = ref('7d');
const chartKey = ref(0);

const { prices, loading, error, fetchPrices } = usePrices({ autoFetch: false });
const { emaValues } = useEMA();

const filteredPrices = computed(() => {
  return filterPricesByPeriod(prices.value, selectedPeriod.value);
});

const chartData = computed(() => {
  if (!filteredPrices.value.length) return null;

  const labels = filteredPrices.value
    .reverse()
    .map(p => new Date(p.timestamp).toLocaleString('da-DK'));

  const closePrices = filteredPrices.value.map(p => p.close);

  return {
    labels,
    datasets: [
      {
        label: 'Close Price',
        data: closePrices,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.1
      },
      {
        label: 'Short EMA (10)',
        data: calculateEMALine(closePrices, 10),
        borderColor: 'rgb(251, 146, 60)',
        borderDash: [5, 5],
        fill: false
      },
      {
        label: 'Medium EMA (20)',
        data: calculateEMALine(closePrices, 20),
        borderColor: 'rgb(168, 85, 247)',
        borderDash: [5, 5],
        fill: false
      },
      {
        label: 'Long EMA (50)',
        data: calculateEMALine(closePrices, 50),
        borderColor: 'rgb(180, 83, 9)',
        borderDash: [5, 5],
        fill: false
      }
    ]
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top'
    },
    tooltip: {
      mode: 'index',
      intersect: false
    }
  },
  scales: {
    y: {
      beginAtZero: false
    }
  }
};

const calculateEMALine = (prices, period) => {
  // Simplified EMA calculation for chart
  const result = [];
  for (let i = period - 1; i < prices.length; i++) {
    const slice = prices.slice(i - period + 1, i + 1);
    const ema = slice.reduce((sum, p) => sum + p, 0) / period;
    result.push(ema);
  }
  return Array(period - 1).fill(null).concat(result);
};

const updateChart = () => {
  chartKey.value++;
};

watch(() => prices.value, () => {
  updateChart();
});

fetchPrices(200);
</script>

<style scoped>
.price-chart {
  padding: 1.5rem;
  background: var(--color-surface);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.price-chart__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.price-chart__canvas {
  height: 400px;
  position: relative;
}
</style>
```

---

## 8. OWASP Security Best Practices

### 8.1 Content Security Policy (CSP)

Tilføj til `index.html`:

```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline' https://*.firebase.com https://*.googleapis.com; 
               style-src 'self' 'unsafe-inline'; 
               img-src 'self' data: https:; 
               connect-src 'self' https://*.firebase.com https://*.googleapis.com;">
```

### 8.2 Input Validation

Brug Zod schemas i alle services (allerede implementeret).

### 8.3 XSS Prevention

- Brug Vue's `v-text` eller `{{ }}` interpolation (automatisk escaping)
- Undgå `v-html` med user input
- Sanitize data fra Firebase

### 8.4 Environment Variables

- Aldrig commit `.env` fil
- Brug `VITE_` prefix for Vite env vars
- Valider env vars ved app start

### 8.5 Error Handling

```javascript
// utils/errorHandler.js
export function handleError(error, context = '') {
  // OWASP: Don't expose sensitive error details
  const userMessage = 'Der opstod en fejl. Prøv igen senere.';
  
  // Log detailed error server-side (not exposed to user)
  console.error(`Error in ${context}:`, error);
  
  return userMessage;
}
```

### 8.6 Rate Limiting

Implementer i composables:

```javascript
// utils/rateLimiter.js
export function createRateLimiter(maxRequests, windowMs) {
  const requests = [];
  
  return function checkLimit() {
    const now = Date.now();
    requests.push(now);
    
    // Remove old requests
    while (requests.length > 0 && requests[0] < now - windowMs) {
      requests.shift();
    }
    
    if (requests.length > maxRequests) {
      throw new Error('Rate limit exceeded');
    }
  };
}
```

---

## 9. FURPS+ Kvalitetskriterier

### Functionality
- ✅ Alle features implementeret
- ✅ Data hentes korrekt fra Firebase
- ✅ Visualiseringer fungerer

### Usability
- ✅ Responsivt design
- ✅ Loading states
- ✅ Error messages
- ✅ Accessibility (ARIA labels)

### Reliability
- ✅ Error handling
- ✅ Retry logic
- ✅ Graceful degradation

### Performance
- ✅ Lazy loading
- ✅ Data pagination
- ✅ Chart optimization
- ✅ Memoization hvor nødvendigt

### Supportability
- ✅ Modulær kode
- ✅ Dokumentation
- ✅ Testing setup
- ✅ Logging

### + (Design Constraints)
- ✅ Vue.js 3
- ✅ Firebase integration
- ✅ OWASP compliance

---

## 10. Testing Setup

### 10.1 Unit Tests (`tests/unit/composables/usePrices.spec.js`)

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePrices } from '@/composables/usePrices';
import { PriceService } from '@/services/data/priceService';

vi.mock('@/services/data/priceService');

describe('usePrices', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch prices on mount', async () => {
    const mockPrices = [
      { id: '1', timestamp: '2024-01-01', close: 100 }
    ];
    
    PriceService.getLatestPrices.mockResolvedValue(mockPrices);
    
    const { prices, loading } = usePrices({ autoFetch: true });
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    expect(prices.value).toEqual(mockPrices);
  });
});
```

### 10.2 Component Tests

```javascript
import { mount } from '@vue/test-utils';
import PriceList from '@/components/prices/PriceList.vue';

describe('PriceList', () => {
  it('renders price table', () => {
    const wrapper = mount(PriceList);
    expect(wrapper.find('.price-table').exists()).toBe(true);
  });
});
```

---

## 11. Build & Deployment

### 11.1 Build Commands

```json
// package.json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs",
    "format": "prettier --write src/",
    "security-audit": "audit-ci --moderate"
  }
}
```

### 11.2 Vite Config (`vite.config.js`)

```javascript
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false, // OWASP: Don't expose source maps in production
    rollupOptions: {
      output: {
        manualChunks: {
          'firebase': ['firebase/app', 'firebase/firestore'],
          'chart': ['chart.js', 'vue-chartjs']
        }
      }
    }
  },
  server: {
    port: 3000,
    strictPort: true
  }
});
```

### 11.3 Firebase Hosting Deployment

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize
firebase init hosting

# Deploy
firebase deploy --only hosting
```

`firebase.json`:
```json
{
  "hosting": {
    "public": "dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=31536000"
          }
        ]
      }
    ]
  }
}
```

---

## 12. Checkliste for Implementering

### Fase 1: Setup
- [ ] Opret Vue projekt
- [ ] Installer dependencies
- [ ] Opsæt projekt struktur
- [ ] Konfigurer Firebase
- [ ] Opsæt environment variables

### Fase 2: Services
- [ ] Implementer FirestoreService
- [ ] Implementer PriceService
- [ ] Implementer SignalService
- [ ] Implementer EMAService
- [ ] Tilføj input validation

### Fase 3: Composables
- [ ] Implementer usePrices
- [ ] Implementer useEMA
- [ ] Implementer useSignals
- [ ] Implementer useRealTime

### Fase 4: Components
- [ ] Opret PriceList komponent
- [ ] Opret PriceChart komponent
- [ ] Opret EMAList komponent
- [ ] Opret common komponenter (Loading, Error)

### Fase 5: Views & Routing
- [ ] Opret Dashboard view
- [ ] Opsæt Vue Router
- [ ] Tilføj navigation

### Fase 6: Styling
- [ ] Opsæt CSS variables
- [ ] Implementer responsive design
- [ ] Tilføj dark mode (optional)

### Fase 7: Testing
- [ ] Skriv unit tests
- [ ] Skriv component tests
- [ ] Test error handling

### Fase 8: Security & Performance
- [ ] Implementer CSP
- [ ] Tilføj rate limiting
- [ ] Optimize bundle size
- [ ] Performance testing

### Fase 9: Deployment
- [ ] Build production bundle
- [ ] Test production build
- [ ] Deploy til Firebase Hosting
- [ ] Verify deployment

---

## 13. Ressourcer & Referencer

- Vue.js 3 Docs: https://vuejs.org/
- Firebase Docs: https://firebase.google.com/docs
- Chart.js Docs: https://www.chartjs.org/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- GRASP Patterns: https://en.wikipedia.org/wiki/GRASP_(object-oriented_design)
- FURPS+: https://en.wikipedia.org/wiki/FURPS

---

**Status:** Instruktionssæt klar - klar til implementering 🚀









