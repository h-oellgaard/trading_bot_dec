import time
import requests
from datetime import datetime
from src.domain.strategy import MarketData

class DataService:
    def __init__(self, symbol="bitcoin", interval=60):
        self.symbol = symbol
        self.interval = interval
        self.prices = []
        self.volume = []
        self.timestamp = []
        self.last_request_time = 0
        print(f"Initializing DataService for {symbol}")
        print(f"Data interval: {interval} seconds")

    def _wait_for_rate_limit(self):
        """Ensure we don't exceed API rate limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < 1.5:  # CoinGecko has a rate limit of ~50 calls per minute
            time.sleep(1.5 - time_since_last_request)
        self.last_request_time = time.time()

    def fetch_data(self):
        """Fetch real data from CoinGecko API with error handling"""
        self._wait_for_rate_limit()
        
        try:
            # Use markets endpoint which is more reliable
            url = f"https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'ids': self.symbol,
                'order': 'market_cap_desc',
                'per_page': 1,
                'page': 1,
                'sparkline': False
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise exception for non-200 status codes
            data = response.json()
            
            if not data:
                raise ValueError(f"No data returned for symbol '{self.symbol}'")
            
            coin_data = data[0]
            price = coin_data['current_price']
            volume = coin_data['total_volume']
            current_time = time.time()
            
            self.prices.append(price)
            self.volume.append(volume)
            self.timestamp.append(current_time)
            
            # Keep only last 100 data points (increased from 20)
            if len(self.prices) > 100:
                self.prices = self.prices[-100:]
                self.volume = self.volume[-100:]
                self.timestamp = self.timestamp[-100:]
            
            return MarketData(self.prices, self.volume, self.timestamp)
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {str(e)}")
            # Return last known data if available, otherwise raise
            if self.prices:
                return MarketData(self.prices, self.volume, self.timestamp)
            raise
        except (KeyError, ValueError) as e:
            print(f"Data parsing error: {str(e)}")
            if self.prices:
                return MarketData(self.prices, self.volume, self.timestamp)
            raise

    def get_time_since_last_update(self):
        """Get time elapsed since last data update"""
        if not self.timestamp:
            return float('inf')
        return time.time() - self.timestamp[-1]

    def run(self):
        print("Starting data service. Press Ctrl+C to stop.")
        try:
            while True:
                try:
                    market_data = self.fetch_data()
                    elapsed = self.get_time_since_last_update()
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Price=${market_data.prices[-1]:,.2f}, "
                          f"Volume=${market_data.volume[-1]:,.2f}, "
                          f"Data age: {elapsed:.1f}s")
                    time.sleep(self.interval)
                except Exception as e:
                    print(f"Error: {str(e)}")
                    time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\nData service stopped.")

if __name__ == "__main__":
    service = DataService()
    service.run() 