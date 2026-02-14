"""
Trader module for executing trades via Firi API.
Handles order placement and management.
"""
import os
import hmac
import hashlib
import time
import uuid
import json
from datetime import datetime
from typing import Optional
import httpx
from dotenv import load_dotenv

from models import Trade, TradeStatus

load_dotenv()


def round_price(price: float, decimals: int = 2) -> float:
    """Round price to specified decimals (e.g. 2 for DKK)."""
    return round(price, decimals)


def round_quantity(quantity: float, decimals: int = 8) -> float:
    """Round quantity to specified decimals (e.g. 8 for BTC)."""
    return round(quantity, decimals)


class FiriTrader:
    """Handles trade execution via Firi API."""

    PRICE_DECIMALS = 2    # Fiat (DKK) typically 2 decimals
    QUANTITY_DECIMALS = 8  # BTC typically 8 decimals (satoshi precision)

    def __init__(self):
        self.api_key = os.getenv("FIRI_API_KEY")
        self.secret = os.getenv("FIRI_SECRET")
        self.client_id = os.getenv("FIRI_CLIENT_ID")  # Optional client ID
        self.base_url = os.getenv("FIRI_BASE_URL", "https://api.firi.com")
        self.price_decimals = int(os.getenv("PRICE_DECIMALS", str(self.PRICE_DECIMALS)))
        self.quantity_decimals = int(os.getenv("QUANTITY_DECIMALS", str(self.QUANTITY_DECIMALS)))

        if not self.api_key or not self.secret:
            raise ValueError("FIRI_API_KEY and FIRI_SECRET must be set in .env")
    
    def _generate_signature(self, timestamp: str, validity: str, body_dict: dict = None) -> str:
        """
        Generate HMAC signature for Firi API authentication.
        Firi uses: HMAC_SHA256(JSON.stringify({timestamp, validity, ...requestBody}))
        """
        import json
        
        # Base body with timestamp and validity as strings
        signature_body = {
            "timestamp": timestamp,
            "validity": validity
        }
        
        # Add request body fields if provided (for POST requests)
        if body_dict:
            signature_body.update(body_dict)
        
        # Convert to JSON string (sorted keys for consistency)
        message = json.dumps(signature_body, sort_keys=True, separators=(',', ':'))
        
        signature = hmac.new(
            self.secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers_and_params(self, method: str, body_dict: dict = None) -> tuple:
        """
        Generate authentication headers and query parameters for Firi API.
        Returns: (headers_dict, query_params_dict)
        """
        # Timestamp in SECONDS (epoch), not milliseconds!
        timestamp = str(int(time.time()))
        validity = "2000"  # 2000 seconds validity
        
        signature = self._generate_signature(timestamp, validity, body_dict)
        
        headers = {
            "firi-user-signature": signature,
            "Content-Type": "application/json"
        }
        
        # Add client ID header (required for HMAC auth)
        if self.client_id:
            headers["firi-user-clientid"] = self.client_id
        else:
            raise ValueError("FIRI_CLIENT_ID must be set for HMAC authentication")
        
        # Query parameters (required for HMAC auth)
        query_params = {
            "timestamp": timestamp,
            "validity": validity
        }
        
        return headers, query_params
    
    def get_balance(self, currency: str = "DKK") -> float:
        """
        Get account balance for a specific currency.
        
        Args:
            currency: Currency code (e.g., "NOK", "BTC")
            
        Returns:
            Available balance
        """
        # Try v2 endpoint first, fallback to v1 if needed
        path = "/v2/balances"
        headers, query_params = self._get_headers_and_params("GET")
        
        try:
            response = httpx.get(
                f"{self.base_url}{path}",
                headers=headers,
                params=query_params,
                timeout=30.0
            )
            
            # If v2 fails with 401, try v1
            if response.status_code == 401:
                path = "/v1/balances"
                headers, query_params = self._get_headers_and_params("GET")
                response = httpx.get(
                    f"{self.base_url}{path}",
                    headers=headers,
                    params=query_params,
                    timeout=30.0
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Firi API returns balances as a list: [{"currency": "string", "balance": "string", "hold": "string", "available": "string"}]
            if isinstance(data, list):
                balances = data
            elif isinstance(data, dict):
                balances = data.get("data", [])
            else:
                balances = []
            
            for balance in balances:
                if isinstance(balance, dict):
                    if balance.get("currency") == currency:
                        # Firi returns amounts as strings
                        return float(balance.get("available", balance.get("balance", "0")))
            
            return 0.0
            
        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch balance from Firi API: {e}")
    
    def place_buy_order(
        self,
        pair: str,
        quantity: float,
        price: Optional[float] = None
    ) -> Trade:
        """
        Place a buy order.
        
        Args:
            pair: Trading pair (e.g., "BTC/NOK")
            quantity: Quantity to buy (in base currency, e.g., BTC)
            price: Required price (Firi API requires price even for market orders)
            
        Returns:
            Trade object
        """
        if not price or price <= 0:
            raise ValueError("Price is required and must be greater than 0")
        
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")

        price = round_price(price, self.price_decimals)
        quantity = round_quantity(quantity, self.quantity_decimals)
        
        firi_pair = pair.replace("/", "")
        path = "/v2/orders"
        
        # Firi API uses "bid" for buy orders, "ask" for sell orders
        # type must be "bid" or "ask", not "buy" or "sell"
        order_data = {
            "market": firi_pair,
            "type": "bid",  # "bid" = buy order
            "price": str(price),  # Price is required by Firi API
            "amount": str(quantity)  # Firi uses "amount" not "quantity"
        }
        
        # For POST requests, order data must be included in signature
        headers, query_params = self._get_headers_and_params("POST", order_data)
        
        try:
            response = httpx.post(
                f"{self.base_url}{path}",
                headers=headers,
                params=query_params,
                json=order_data,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract order information from response
            # Firi API returns: {"id": 0} for successful order creation
            order_id = str(data.get("id", str(uuid.uuid4())))
            # For market orders, we need to fetch the order details to get executed price
            # For now, use the requested price or fetch from order details
            executed_price = float(price) if price else 0.0
            executed_quantity = float(quantity)
            
            return Trade(
                trade_id=order_id,
                pair=pair,
                side="buy",
                price=executed_price,
                quantity=executed_quantity,
                status=TradeStatus.OPEN,
                timestamp=datetime.now()
            )
            
        except httpx.HTTPError as e:
            raise Exception(f"Failed to place buy order on Firi API: {e}")
    
    def place_sell_order(
        self,
        pair: str,
        quantity: float,
        price: Optional[float] = None
    ) -> Trade:
        """
        Place a sell order.
        
        Args:
            pair: Trading pair (e.g., "BTC/NOK")
            quantity: Quantity to sell (in base currency, e.g., BTC)
            price: Required price (Firi API requires price even for market orders)
            
        Returns:
            Trade object
        """
        if not price or price <= 0:
            raise ValueError("Price is required and must be greater than 0")
        
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")

        price = round_price(price, self.price_decimals)
        quantity = round_quantity(quantity, self.quantity_decimals)
        
        firi_pair = pair.replace("/", "")
        path = "/v2/orders"
        
        # Firi API uses "bid" for buy orders, "ask" for sell orders
        order_data = {
            "market": firi_pair,
            "type": "ask",  # "ask" = sell order
            "price": str(price),  # Price is required by Firi API
            "amount": str(quantity)  # Firi uses "amount" not "quantity"
        }
        
        # For POST requests, order data must be included in signature
        headers, query_params = self._get_headers_and_params("POST", order_data)
        
        try:
            response = httpx.post(
                f"{self.base_url}{path}",
                headers=headers,
                params=query_params,
                json=order_data,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract order information from response
            # Firi API returns: {"id": 0} for successful order creation
            order_id = str(data.get("id", str(uuid.uuid4())))
            # For market orders, we need to fetch the order details to get executed price
            executed_price = float(price) if price else 0.0
            executed_quantity = float(quantity)
            
            return Trade(
                trade_id=order_id,
                pair=pair,
                side="sell",
                price=executed_price,
                quantity=executed_quantity,
                status=TradeStatus.OPEN,
                timestamp=datetime.now()
            )
            
        except httpx.HTTPError as e:
            raise Exception(f"Failed to place sell order on Firi API: {e}")
    
    def get_open_orders(self, pair: Optional[str] = None) -> list[dict]:
        """
        Get list of open orders.
        
        Args:
            pair: Optional trading pair to filter by
            
        Returns:
            List of open order dictionaries
        """
        path = "/v2/orders"
        # Firi API doesn't use status parameter, it returns all active orders
        full_path = path
        if pair:
            firi_pair = pair.replace("/", "")
            full_path = f"/v2/orders/{firi_pair}"
        
        headers, query_params = self._get_headers_and_params("GET")
        
        try:
            response = httpx.get(
                f"{self.base_url}{full_path}",
                headers=headers,
                params=query_params,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("data", data) if isinstance(data, dict) else data
            
        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch open orders from Firi API: {e}")
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successful
        """
        path = f"/v2/orders/{order_id}/detailed"
        headers, query_params = self._get_headers_and_params("DELETE")
        
        try:
            response = httpx.delete(
                f"{self.base_url}{path}",
                headers=headers,
                params=query_params,
                timeout=30.0
            )
            response.raise_for_status()
            return True
            
        except httpx.HTTPError as e:
            raise Exception(f"Failed to cancel order on Firi API: {e}")

