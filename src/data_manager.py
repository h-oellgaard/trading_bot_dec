import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from threading import Thread, Event

from .data_service import DataService
from .infrastructure.firestore_repository import FirestorePriceDataRepository, FirestoreTradeRepository
from .domain.repository import PriceData, MarketData
from .domain.trade import Trade
from .domain.coin import Coin


logger = logging.getLogger(__name__)


class DataManager:
    """Manages data persistence and retrieval using Firestore"""
    
    def __init__(self, project_id: Optional[str] = None, 
                 price_collection: str = "price_data",
                 trade_collection: str = "trades"):
        """
        Initialize the data manager with Firestore repositories
        
        Args:
            project_id: Google Cloud project ID (uses default if None)
            price_collection: Firestore collection name for price data
            trade_collection: Firestore collection name for trade data
        """
        self.price_repository = FirestorePriceDataRepository(
            project_id=project_id, 
            collection_name=price_collection
        )
        self.trade_repository = FirestoreTradeRepository(
            project_id=project_id, 
            collection_name=trade_collection
        )
        self.data_service = DataService()
        
        # Background data collection
        self._collection_thread = None
        self._stop_event = Event()
        self._collection_interval = 60  # seconds
        
        logger.info("DataManager initialized with Firestore repositories")
    
    def start_data_collection(self, symbols: List[str], interval: int = 60):
        """
        Start background data collection for specified symbols
        
        Args:
            symbols: List of cryptocurrency symbols to collect data for
            interval: Collection interval in seconds
        """
        if self._collection_thread and self._collection_thread.is_alive():
            logger.warning("Data collection already running")
            return
        
        self._collection_interval = interval
        self._stop_event.clear()
        self._collection_thread = Thread(
            target=self._collect_data_loop,
            args=(symbols,),
            daemon=True
        )
        self._collection_thread.start()
        logger.info(f"Started data collection for {symbols} every {interval} seconds")
    
    def stop_data_collection(self):
        """Stop background data collection"""
        if self._collection_thread and self._collection_thread.is_alive():
            self._stop_event.set()
            self._collection_thread.join(timeout=5)
            logger.info("Stopped data collection")
    
    def _collect_data_loop(self, symbols: List[str]):
        """Background loop for data collection"""
        while not self._stop_event.is_set():
            try:
                for symbol in symbols:
                    self._collect_symbol_data(symbol)
                
                # Wait for next collection cycle
                self._stop_event.wait(self._collection_interval)
                
            except Exception as e:
                logger.error(f"Error in data collection loop: {e}")
                # Wait a bit before retrying
                self._stop_event.wait(10)
    
    def _collect_symbol_data(self, symbol: str):
        """Collect and store data for a single symbol"""
        try:
            # Fetch current price data
            price_data = self.data_service.get_current_price(symbol)
            if price_data:
                # Convert to domain model
                domain_price_data = PriceData(
                    symbol=symbol,
                    price=price_data['price'],
                    volume=price_data.get('volume', 0.0),
                    timestamp=datetime.now(),
                    source='coingecko'
                )
                
                # Save to Firestore
                success = self.price_repository.save_price_data(domain_price_data)
                if success:
                    logger.debug(f"Saved price data for {symbol}: ${price_data['price']}")
                else:
                    logger.warning(f"Failed to save price data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error collecting data for {symbol}: {e}")
    
    def get_market_data(self, symbol: str, periods: int) -> Optional[MarketData]:
        """
        Get market data for strategy analysis
        
        Args:
            symbol: Cryptocurrency symbol
            periods: Number of periods to retrieve
            
        Returns:
            MarketData object or None if insufficient data
        """
        try:
            # First try to get from Firestore
            market_data = self.price_repository.get_market_data(symbol, periods)
            
            if market_data and len(market_data) >= periods:
                logger.debug(f"Retrieved {len(market_data)} periods for {symbol} from Firestore")
                return market_data
            
            # If insufficient data in Firestore, fetch from API
            logger.info(f"Insufficient data in Firestore for {symbol}, fetching from API")
            return self._fetch_and_store_historical_data(symbol, periods)
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def _fetch_and_store_historical_data(self, symbol: str, periods: int) -> Optional[MarketData]:
        """Fetch historical data from API and store in Firestore"""
        try:
            # Fetch historical data from API
            historical_data = self.data_service.get_historical_data(symbol, days=periods)
            
            if not historical_data or len(historical_data) < periods:
                logger.warning(f"Insufficient historical data for {symbol}")
                return None
            
            # Convert to domain models and store
            price_data_list = []
            for data_point in historical_data:
                price_data = PriceData(
                    symbol=symbol,
                    price=data_point['price'],
                    volume=data_point.get('volume', 0.0),
                    timestamp=datetime.fromtimestamp(data_point['timestamp'] / 1000),
                    source='coingecko'
                )
                price_data_list.append(price_data)
            
            # Save to Firestore
            success = self.price_repository.save_batch_price_data(price_data_list)
            if success:
                logger.info(f"Stored {len(price_data_list)} historical data points for {symbol}")
            
            # Return market data for immediate use
            prices = [pd.price for pd in price_data_list]
            volumes = [pd.volume for pd in price_data_list]
            timestamps = [pd.timestamp for pd in price_data_list]
            
            return MarketData(
                symbol=symbol,
                prices=prices,
                volumes=volumes,
                timestamps=timestamps
            )
            
        except Exception as e:
            logger.error(f"Error fetching and storing historical data for {symbol}: {e}")
            return None
    
    def save_trade(self, trade: Trade) -> bool:
        """Save a trade to Firestore"""
        try:
            success = self.trade_repository.save_trade(trade)
            if success:
                logger.info(f"Saved trade {trade.id} for {trade.coin.symbol}")
            return success
        except Exception as e:
            logger.error(f"Error saving trade: {e}")
            return False
    
    def get_trades(self, symbol: Optional[str] = None, 
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None,
                  limit: Optional[int] = None) -> List[Trade]:
        """Retrieve trades with optional filters"""
        try:
            return self.trade_repository.get_trades(
                symbol=symbol,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error retrieving trades: {e}")
            return []
    
    def get_trading_statistics(self, symbol: Optional[str] = None,
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get trading statistics"""
        try:
            return self.trade_repository.get_trading_statistics(
                symbol=symbol,
                start_time=start_time,
                end_time=end_time
            )
        except Exception as e:
            logger.error(f"Error retrieving trading statistics: {e}")
            return {}
    
    def get_data_statistics(self, symbol: str) -> Dict[str, Any]:
        """Get statistics about stored data for a symbol"""
        try:
            return self.price_repository.get_data_statistics(symbol)
        except Exception as e:
            logger.error(f"Error retrieving data statistics: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old price data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = self.price_repository.delete_old_data(cutoff_date)
            logger.info(f"Cleaned up {deleted_count} old price data records")
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
    
    def get_available_symbols(self) -> List[str]:
        """Get list of symbols with data in Firestore"""
        try:
            return self.price_repository.get_symbols()
        except Exception as e:
            logger.error(f"Error retrieving available symbols: {e}")
            return []
    
    def get_latest_price(self, symbol: str) -> Optional[PriceData]:
        """Get the most recent price data for a symbol"""
        try:
            return self.price_repository.get_latest_price(symbol)
        except Exception as e:
            logger.error(f"Error retrieving latest price for {symbol}: {e}")
            return None 