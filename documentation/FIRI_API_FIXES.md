# Firi API Fixes Baseret på Dokumentation

## 🔧 Retteelser Foretaget

### 1. Balance Endpoint
- **Før**: `/v1/account/balance` ❌
- **Efter**: `/v1/balances` ✅
- **Kilde**: [Firi API Docs - Balance](https://developers.firi.com/#section/Balance/get-v1-balances)

### 2. Orders Endpoint
- **Før**: `/v1/orders` ❌
- **Efter**: `/v2/orders` ✅
- **Kilde**: [Firi API Docs - Orders](https://developers.firi.com/#section/Order/post-v2-orders)

### 3. Order Format
- **Før**: 
  ```python
  {
    "side": "buy",  # ❌ Forkert
    "type": "limit",
    "quantity": "0.1"
  }
  ```
- **Efter**:
  ```python
  {
    "type": "bid",  # ✅ "bid" = buy, "ask" = sell
    "price": "500000",  # ✅ Required
    "amount": "0.1"  # ✅ "amount" ikke "quantity"
  }
  ```
- **Kilde**: [Firi API Docs - Create Order](https://developers.firi.com/#section/Order/post-v2-orders)

### 4. Cancel Order Endpoint
- **Før**: `/v1/orders/{order_id}` ❌
- **Efter**: `/v2/orders/{order_id}/detailed` ✅
- **Kilde**: [Firi API Docs - Delete Order](https://developers.firi.com/#section/Order/delete-v2-orders-orderID-detailed)

### 5. Get Orders Endpoint
- **Før**: `/v1/orders?status=open` ❌
- **Efter**: `/v2/orders` eller `/v2/orders/{market}` ✅
- **Note**: Firi API returnerer kun aktive orders, ingen status parameter
- **Kilde**: [Firi API Docs - Get Orders](https://developers.firi.com/#section/Order/get-v2-orders)

### 6. Balance Response Parsing
- **Før**: Antog nested struktur
- **Efter**: Parser direkte liste: `[{"currency": "...", "available": "...", ...}]`
- **Note**: Firi returnerer amounts som strings, skal konverteres til float

---

## ⚠️ Vigtige Bemærkninger fra Dokumentationen

### Authentication Errors
Fra [Firi API Error Docs](https://developers.firi.com/#section/Errors-and-problems/Error-messages:-Access-control-(AuthorizationAuthentication)):

1. **Invalid Signature**: 
   - "The hmac encrypted secretKey did not match"
   - **PS! Timestamp and validity has to be strings** ✅ (Vi gør dette korrekt)

2. **Expired Signature**:
   - "Make sure the timestamp was not made in the past"
   - Vi bruger `time.time() * 1000` hvilket er korrekt

### Order Response
- Firi API returnerer kun `{"id": 0}` ved order creation
- For at få executed price/quantity skal man fetche order details via `/v2/order/{orderID}`
- **TODO**: Implementer order detail fetching efter order creation

---

## 🔍 Manglende Features

### Order Detail Fetching
Efter order creation skal vi fetche order details for at få faktisk executed price:
```python
GET /v2/order/{orderID}
```

### Market Orders
- Firi API kræver `price` parameter selv for market orders
- Vi skal håndtere dette korrekt - måske bruge current market price

---

## ✅ Status

- ✅ Balance endpoint rettet
- ✅ Orders endpoint rettet  
- ✅ Order format rettet (bid/ask, amount)
- ✅ Cancel order endpoint rettet
- ✅ Balance parsing rettet
- ⚠️ Order detail fetching mangler (kan tilføjes senere)
- ⚠️ Market order price handling skal testes










