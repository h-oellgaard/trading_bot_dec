# API Endpoints Opdatering

## Opdateret Endpoints til v2

### Market History Endpoint
- **Før**: `/v1/markets/{market}/candles` ❌
- **Efter**: `/v2/markets/{market}/history` ✅
- **Kilde**: Bruger henvisning til Firi API v2 endpoint

### Andre Endpoints (Allerede Opdateret)
- ✅ Balance: `/v1/balances` eller `/v2/balances`
- ✅ Orders: `/v2/orders`
- ✅ Cancel Order: `/v2/orders/{orderID}/detailed`

---

## Bemærkninger

- Market history endpoint kan have forskelligt response format i v2
- Response parsing kan kræve justeringer baseret på faktisk API response
- Test endpoint før produktion










