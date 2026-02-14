"""
Data fetcher module for retrieving OHLC data from Firi API.
Pure data fetching with no business logic.
"""
import os
import logging
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from typing import List, Optional
from collections import defaultdict
import httpx
from dotenv import load_dotenv

from models import Candle

load_dotenv()

logger = logging.getLogger(__name__)


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
    
    def _convert_trade_history_to_ohlc(
        self,
        trades: List[dict],
        interval: str
    ) -> List[Candle]:
        """
        Convert trade history to OHLC candles.
        
        Args:
            trades: List of trade dictionaries with timestamp and price
            interval: Candle interval (e.g., "1h", "1m", "4h", "1d")
            
        Returns:
            List of Candle objects
        """
        if not trades:
            return []
        
        # Parse interval to timedelta
        interval_map = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1),
        }
        interval_delta = interval_map.get(interval, timedelta(hours=1))
        
        # Group trades by candle period
        candles_dict = defaultdict(lambda: {
            "open": None,
            "high": None,
            "low": None,
            "close": None,
            "volume": 0.0,
            "timestamp": None
        })
        
        processed_count = 0
        skipped_count = 0
        
        for trade in trades:
            try:
                # Parse timestamp - try multiple possible keys
                trade_time = None
                timestamp_value = trade.get("timestamp") or trade.get("created_at") or trade.get("time") or trade.get("date")
                
                if timestamp_value is None:
                    skipped_count += 1
                    continue
                
                if isinstance(timestamp_value, (int, float)):
                    # Unix timestamp in seconds or milliseconds
                    ts = timestamp_value
                    if ts > 1e10:  # Milliseconds
                        ts = ts / 1000
                    trade_time = datetime.fromtimestamp(ts, tz=None)
                elif isinstance(timestamp_value, str):
                    # Handle ISO format strings
                    timestamp_str = timestamp_value.replace("Z", "+00:00")
                    try:
                        trade_time = datetime.fromisoformat(timestamp_str)
                    except ValueError:
                        # Try parsing with different formats
                        try:
                            trade_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f%z")
                        except ValueError:
                            trade_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S%z")
                else:
                    skipped_count += 1
                    continue
                
                # Get price
                price = float(trade.get("price", trade.get("rate", 0)))
                if price <= 0:
                    skipped_count += 1
                    continue
                
                # Get volume
                volume = float(trade.get("amount", trade.get("quantity", trade.get("volume", 0))))
                
                # Calculate candle start time (round down to interval)
                if interval_delta >= timedelta(days=1):
                    # Daily candles: round to midnight
                    candle_start = trade_time.replace(hour=0, minute=0, second=0, microsecond=0)
                elif interval_delta >= timedelta(hours=1):
                    # Hourly candles: round to hour
                    candle_start = trade_time.replace(minute=0, second=0, microsecond=0)
                else:
                    # Minute candles: round down to interval
                    interval_minutes = int(interval_delta.total_seconds() / 60)
                    rounded_minutes = (trade_time.minute // interval_minutes) * interval_minutes
                    candle_start = trade_time.replace(minute=rounded_minutes, second=0, microsecond=0)
                
                candle_key = candle_start.isoformat()
                candle = candles_dict[candle_key]
                
                # Update OHLC
                if candle["open"] is None:
                    candle["open"] = price
                    candle["timestamp"] = candle_start
                
                if candle["high"] is None or price > candle["high"]:
                    candle["high"] = price
                
                if candle["low"] is None or price < candle["low"]:
                    candle["low"] = price
                
                candle["close"] = price
                candle["volume"] += volume
                processed_count += 1
                
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Error processing trade: {e}, trade: {trade}")
                skipped_count += 1
                continue
        
        logger.info(f"Processed {processed_count} trades, skipped {skipped_count} trades")
        
        # Convert to Candle objects
        candles = []
        for candle_data in candles_dict.values():
            if candle_data["open"] is not None:
                candles.append(Candle(
                    timestamp=candle_data["timestamp"],
                    open=candle_data["open"],
                    high=candle_data["high"],
                    low=candle_data["low"],
                    close=candle_data["close"],
                    volume=candle_data["volume"]
                ))
        
        # Sort by timestamp (oldest first)
        candles.sort(key=lambda c: c.timestamp)
        
        return candles
    
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
            pair: Trading pair (e.g., "BTC/DKK")
            interval: Candle interval (e.g., "1h", "30m", "4h", "1d")
            limit: Maximum number of candles to fetch
            start_time: Optional start time
            end_time: Optional end time
            
        Returns:
            List of Candle objects sorted by timestamp (oldest first)
        """
        # Try different market formats
        market_formats = [
            pair.replace("/", ""),  # BTCDKK
            pair.replace("/", "-"),  # BTC-DKK
            pair.replace("/", "").lower(),  # btcdkk
            pair.replace("/", "-").lower(),  # btc-dkk
        ]
        
        # Also try NOK if DKK doesn't work
        if "DKK" in pair:
            market_formats.extend([
                pair.replace("DKK", "NOK").replace("/", ""),  # BTCNOK
                pair.replace("DKK", "NOK").replace("/", "-"),  # BTC-NOK
            ])
        
        logger.info(f"Trying to fetch candles for pair {pair}, will try formats: {market_formats}")
        
        for market_format in market_formats:
            try:
                # Use v2/markets/{market}/history endpoint
                url = f"{self.base_url}/v2/markets/{market_format}/history"
                
                params = {
                    "interval": interval,
                    "limit": limit
                }
                
                response = httpx.get(url, params=params, timeout=30.0)
                
                if response.status_code == 404:
                    # Try next format
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Successfully fetched candles using market format: {market_format}")
                
                # Check if response is trade history format (list of trades)
                if isinstance(data, list) and len(data) > 0:
                    # Check if first item looks like a trade
                    first_item = data[0]
                    if isinstance(first_item, dict) and ("price" in first_item or "rate" in first_item):
                        # Check if it's already OHLC format (has open, high, low, close)
                        if all(key in first_item for key in ["open", "high", "low", "close"]):
                            logger.info(f"Detected OHLC candle format, parsing directly")
                        else:
                            logger.info(f"Detected trade history format, converting to OHLC candles for interval: {interval}")
                            logger.info(f"First trade sample: {first_item}")
                            candles = self._convert_trade_history_to_ohlc(data, interval)
                            logger.info(f"Successfully converted {len(candles)} OHLC candles from trade history")
                            if len(candles) == 0:
                                logger.warning(f"Conversion resulted in 0 candles. Total trades: {len(data)}")
                                logger.warning(f"Sample trades (first 3): {data[:3]}")
                            if candles:
                                candles.sort(key=lambda c: c.timestamp)
                                return candles
                
                # Try to parse as OHLC format
                candles = []
                if isinstance(data, dict):
                    candle_data = data.get("data", data.get("candles", data.get("history", [])))
                else:
                    candle_data = data
                
                for item in candle_data:
                    try:
                        # Firi API typically returns: [timestamp, open, high, low, close, volume]
                        # Or: {"timestamp": ..., "open": ..., "high": ..., "low": ..., "close": ..., "volume": ...}
                        if isinstance(item, list) and len(item) >= 5:
                            timestamp_ms, open_price, high_price, low_price, close_price = item[:5]
                            volume = item[5] if len(item) > 5 else 0.0
                            
                            if timestamp_ms > 1e10:  # Milliseconds
                                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                            else:
                                timestamp = datetime.fromtimestamp(timestamp_ms)
                        elif isinstance(item, dict):
                            timestamp_str = item.get("timestamp", item.get("time", ""))
                            if isinstance(timestamp_str, (int, float)):
                                if timestamp_str > 1e10:  # Milliseconds
                                    timestamp = datetime.fromtimestamp(timestamp_str / 1000)
                                else:
                                    timestamp = datetime.fromtimestamp(timestamp_str)
                            else:
                                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                            
                            open_price = float(item.get("open", item.get("o", 0)))
                            high_price = float(item.get("high", item.get("h", 0)))
                            low_price = float(item.get("low", item.get("l", 0)))
                            close_price = float(item.get("close", item.get("c", 0)))
                            volume = float(item.get("volume", item.get("v", 0)))
                        else:
                            continue
                        
                        candle = Candle(
                            timestamp=timestamp,
                            open=open_price,
                            high=high_price,
                            low=low_price,
                            close=close_price,
                            volume=volume
                        )
                        candles.append(candle)
                    except (KeyError, ValueError, IndexError, TypeError) as e:
                        logger.debug(f"Error parsing candle item: {e}")
                        continue
                
                if candles:
                    # Sort by timestamp (oldest first)
                    candles.sort(key=lambda c: c.timestamp)
                    return candles
                
            except httpx.HTTPError as e:
                if e.response.status_code == 404:
                    # Try next format
                    continue
                logger.warning(f"HTTP error for format {market_format}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error fetching candles for format {market_format}: {e}")
                continue
        
        # If all formats failed, raise exception
        raise Exception(f"Failed to fetch candles from Firi API for pair {pair} with any market format")
    
    def get_ticker_price(self, pair: str) -> Optional[float]:
        """
        Get current price from ticker (order book bid/ask).
        Updates even without trades - uses live order book.
        Public endpoint, no auth required.

        Args:
            pair: Trading pair (e.g., "BTC/DKK")

        Returns:
            Mid-price (bid+ask)/2 or None if unavailable
        """
        market_formats = [
            pair.replace("/", ""),
            pair.replace("/", "-"),
            pair.replace("/", "").lower(),
            pair.replace("/", "-").lower(),
        ]
        if "DKK" in pair:
            market_formats.extend([
                pair.replace("DKK", "NOK").replace("/", ""),
                pair.replace("DKK", "NOK").replace("/", "-"),
            ])

        for market_format in market_formats:
            try:
                url = f"{self.base_url}/v2/markets/{market_format}/ticker"
                response = httpx.get(url, timeout=10.0)
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                data = response.json()
                bid = float(data.get("bid", 0))
                ask = float(data.get("ask", 0))
                if bid > 0 and ask > 0:
                    return (bid + ask) / 2
                if bid > 0:
                    return bid
                if ask > 0:
                    return ask
            except Exception as e:
                logger.debug(f"Ticker fetch failed for {market_format}: {e}")
                continue
        return None

    def get_current_price(self, pair: str) -> Optional[float]:
        """
        Get current price for a trading pair.
        Tries ticker first (live order book), then falls back to trade history.
        """
        price = self.get_ticker_price(pair)
        if price is not None:
            return price
        try:
            candles = self.get_candles(pair=pair, interval="1m", limit=1)
            if candles:
                return candles[-1].close
            return None
        except Exception as e:
            logger.warning(f"Error getting current price: {e}")
            return None
    
    def get_latest_price(self, pair: str) -> float:
        """
        Get the latest price for a trading pair.
        
        Args:
            pair: Trading pair (e.g., "BTC/NOK")
            
        Returns:
            Latest price as float
        """
        price = self.get_current_price(pair)
        if price is None:
            raise Exception(f"No price data available for {pair}")
        return price


