"""
Trader module for executing trades via Firi API.
Handles order placement and management.
"""
import os
import hmac
import hashlib
import time
import uuid
from datetime import datetime
from typing import Optional
import httpx
from dotenv import load_dotenv

from models import Trade, TradeStatus

load_dotenv()


class FiriTrader:
    """Handles trade execution via Firi API."""
    
    def __init__(self):
        self.api_key = os.getenv("FIRI_API_KEY")
        self.secret = os.getenv("FIRI_SECRET")
        self.base_url = os.getenv("FIRI_BASE_URL", "https://api.firi.com")
        
        if not self.api_key or not self.secret:
            raise ValueError("FIRI_API_KEY and FIRI_SECRET must be set in .env")
    
    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate HMAC signature for Firi API authentication."""
        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers(self, method: str, path: str, body: str = "") -> dict:
        """Generate authentication headers for Firi API."""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, method, path, body)
        
        return {
            "X-API-KEY": self.api_key,
            "X-TIMESTAMP": timestamp,
            "X-SIGNATURE": signature,
            "Content-Type": "application/json"
        }
    
    def get_balance(self, currency: str = "NOK") -> float:
        """
        Get account balance for a specific currency.
        
        Args:
            currency: Currency code (e.g., "NOK", "BTC")
            
        Returns:
            Available balance
        """
        path = "/v1/account/balance"
        headers = self._get_headers("GET", path)
        
        try:
            response = httpx.get(
                f"{self.base_url}{path}",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            # Firi API typically returns balances as a list or dict
            if isinstance(data, dict):
                balances = data.get("data", data.get("balances", []))
            else:
                balances = data
            
            for balance in balances:
                if isinstance(balance, dict):
                    if balance.get("currency") == currency or balance.get("asset") == currency:
                        return float(balance.get("available", balance.get("balance", 0.0)))
            
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
            price: Optional limit price (if None, market order)
            
        Returns:
            Trade object
        """
        firi_pair = pair.replace("/", "")
        path = "/v1/orders"
        
        order_data = {
            "market": firi_pair,
            "side": "buy",
            "type": "limit" if price else "market",
            "quantity": str(quantity)
        }
        
        if price:
            order_data["price"] = str(price)
        
        body = str(order_data).replace("'", '"')
        headers = self._get_headers("POST", path, body)
        
        try:
            response = httpx.post(
                f"{self.base_url}{path}",
                headers=headers,
                json=order_data,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract order information from response
            order_id = data.get("id", data.get("order_id", str(uuid.uuid4())))
            executed_price = float(data.get("price", data.get("executed_price", price or 0.0)))
            executed_quantity = float(data.get("quantity", data.get("executed_quantity", quantity)))
            
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
            price: Optional limit price (if None, market order)
            
        Returns:
            Trade object
        """
        firi_pair = pair.replace("/", "")
        path = "/v1/orders"
        
        order_data = {
            "market": firi_pair,
            "side": "sell",
            "type": "limit" if price else "market",
            "quantity": str(quantity)
        }
        
        if price:
            order_data["price"] = str(price)
        
        body = str(order_data).replace("'", '"')
        headers = self._get_headers("POST", path, body)
        
        try:
            response = httpx.post(
                f"{self.base_url}{path}",
                headers=headers,
                json=order_data,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract order information from response
            order_id = data.get("id", data.get("order_id", str(uuid.uuid4())))
            executed_price = float(data.get("price", data.get("executed_price", price or 0.0)))
            executed_quantity = float(data.get("quantity", data.get("executed_quantity", quantity)))
            
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
        path = "/v1/orders"
        params = {"status": "open"}
        if pair:
            params["market"] = pair.replace("/", "")
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_path = f"{path}?{query_string}"
        
        headers = self._get_headers("GET", full_path)
        
        try:
            response = httpx.get(
                f"{self.base_url}{full_path}",
                headers=headers,
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
        path = f"/v1/orders/{order_id}"
        headers = self._get_headers("DELETE", path)
        
        try:
            response = httpx.delete(
                f"{self.base_url}{path}",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            return True
            
        except httpx.HTTPError as e:
            raise Exception(f"Failed to cancel order on Firi API: {e}")

