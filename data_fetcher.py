"""
Data fetcher module for retrieving OHLC data from Firi API.
Pure data fetching with no business logic.
"""
import os
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from typing import List, Optional
import httpx
from dotenv import load_dotenv

from models import Candle

load_dotenv()


class FiriDataFetcher:
    """Fetches OHLC candle data from Firi API."""
    
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
    
    def get_candles(
        self,
        pair: str,
        interval: str = "1h",
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Candle]:
        """
        Fetch OHLC candles from Firi API.
        
        Args:
            pair: Trading pair (e.g., "BTC/NOK")
            interval: Candle interval (e.g., "1h", "4h", "1d")
            limit: Maximum number of candles to fetch
            start_time: Optional start time
            end_time: Optional end time
            
        Returns:
            List of Candle objects
        """
        # Convert pair format from BTC/NOK to BTCNOK or BTC-NOK as needed by Firi
        # Firi typically uses format like "BTCNOK" or "BTC-NOK"
        firi_pair = pair.replace("/", "")
        
        path = f"/v1/markets/{firi_pair}/candles"
        params = {
            "interval": interval,
            "limit": limit
        }
        
        if start_time:
            params["start"] = int(start_time.timestamp())
        if end_time:
            params["end"] = int(end_time.timestamp())
        
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
            
            candles = []
            # Firi API typically returns candles in format:
            # [timestamp, open, high, low, close, volume]
            for candle_data in data.get("data", []):
                if isinstance(candle_data, list) and len(candle_data) >= 5:
                    candles.append(Candle(
                        timestamp=datetime.fromtimestamp(candle_data[0] / 1000),
                        open=float(candle_data[1]),
                        high=float(candle_data[2]),
                        low=float(candle_data[3]),
                        close=float(candle_data[4]),
                        volume=float(candle_data[5]) if len(candle_data) > 5 else 0.0
                    ))
                elif isinstance(candle_data, dict):
                    # Alternative format if API returns objects
                    candles.append(Candle(
                        timestamp=datetime.fromtimestamp(candle_data["timestamp"] / 1000),
                        open=float(candle_data["open"]),
                        high=float(candle_data["high"]),
                        low=float(candle_data["low"]),
                        close=float(candle_data["close"]),
                        volume=float(candle_data.get("volume", 0.0))
                    ))
            
            return candles
            
        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch candles from Firi API: {e}")
    
    def get_latest_price(self, pair: str) -> float:
        """
        Get the latest price for a trading pair.
        
        Args:
            pair: Trading pair (e.g., "BTC/NOK")
            
        Returns:
            Latest price as float
        """
        candles = self.get_candles(pair, interval="1m", limit=1)
        if not candles:
            raise Exception(f"No price data available for {pair}")
        return candles[-1].close

