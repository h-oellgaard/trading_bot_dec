import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

try:
    from google.cloud import firestore
    from google.cloud.firestore import DocumentReference, CollectionReference
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    logging.warning("Firestore not available. Install with: pip install google-cloud-firestore")

from ..domain.repository import (
    PriceDataRepository, TradeRepository, PriceData, MarketData
)
from ..domain.trade import Trade
from ..domain.coin import Coin


logger = logging.getLogger(__name__)


class FirestorePriceDataRepository(PriceDataRepository):
    """Firestore implementation of price data repository"""
    
    def __init__(self, project_id: Optional[str] = None, collection_name: str = "price_data"):
        if not FIRESTORE_AVAILABLE:
            raise ImportError("Firestore not available. Install with: pip install google-cloud-firestore")
        
        self.db = firestore.Client(project=project_id)
        self.collection_name = collection_name
        self.collection: CollectionReference = self.db.collection(collection_name)
        
        logger.info(f"Firestore repository initialized for project: {project_id or 'default'}")
    
    def save_price_data(self, price_data: PriceData) -> bool:
        """Save a single price data point"""
        try:
            # Create document ID from symbol and timestamp
            doc_id = f"{price_data.symbol}_{price_data.timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            doc_ref = self.collection.document(doc_id)
            doc_ref.set({
                'symbol': price_data.symbol,
                'price': price_data.price,
                'volume': price_data.volume,
                'timestamp': price_data.timestamp,
                'source': price_data.source,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            
            logger.debug(f"Saved price data for {price_data.symbol} at {price_data.timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving price data: {e}")
            return False
    
    def save_batch_price_data(self, price_data_list: List[PriceData]) -> bool:
        """Save multiple price data points in batch"""
        if not price_data_list:
            return True
        
        try:
            batch = self.db.batch()
            
            for price_data in price_data_list:
                doc_id = f"{price_data.symbol}_{price_data.timestamp.strftime('%Y%m%d_%H%M%S')}"
                doc_ref = self.collection.document(doc_id)
                
                batch.set(doc_ref, {
                    'symbol': price_data.symbol,
                    'price': price_data.price,
                    'volume': price_data.volume,
                    'timestamp': price_data.timestamp,
                    'source': price_data.source,
                    'created_at': firestore.SERVER_TIMESTAMP
                })
            
            batch.commit()
            logger.info(f"Saved {len(price_data_list)} price data points in batch")
            return True
            
        except Exception as e:
            logger.error(f"Error saving batch price data: {e}")
            return False
    
    def get_price_data(self, symbol: str, start_time: Optional[datetime] = None, 
                      end_time: Optional[datetime] = None, limit: Optional[int] = None) -> List[PriceData]:
        """Retrieve price data for a symbol within a time range"""
        try:
            query = self.collection.where('symbol', '==', symbol)
            
            if start_time:
                query = query.where('timestamp', '>=', start_time)
            
            if end_time:
                query = query.where('timestamp', '<=', end_time)
            
            query = query.order_by('timestamp')
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            
            price_data_list = []
            for doc in docs:
                data = doc.to_dict()
                price_data_list.append(PriceData(
                    symbol=data['symbol'],
                    price=data['price'],
                    volume=data['volume'],
                    timestamp=data['timestamp'],
                    source=data.get('source', 'firestore')
                ))
            
            return price_data_list
            
        except Exception as e:
            logger.error(f"Error retrieving price data: {e}")
            return []
    
    def get_latest_price(self, symbol: str) -> Optional[PriceData]:
        """Get the most recent price data for a symbol"""
        try:
            query = self.collection.where('symbol', '==', symbol).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1)
            docs = list(query.stream())
            
            if docs:
                data = docs[0].to_dict()
                return PriceData(
                    symbol=data['symbol'],
                    price=data['price'],
                    volume=data['volume'],
                    timestamp=data['timestamp'],
                    source=data.get('source', 'firestore')
                )
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving latest price: {e}")
            return None
    
    def get_market_data(self, symbol: str, periods: int) -> Optional[MarketData]:
        """Get market data for a symbol with specified number of periods"""
        try:
            query = self.collection.where('symbol', '==', symbol).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(periods)
            docs = list(query.stream())
            
            if not docs:
                return None
            
            # Reverse to get chronological order
            docs.reverse()
            
            prices = []
            volumes = []
            timestamps = []
            
            for doc in docs:
                data = doc.to_dict()
                prices.append(data['price'])
                volumes.append(data['volume'])
                timestamps.append(data['timestamp'])
            
            return MarketData(
                symbol=symbol,
                prices=prices,
                volumes=volumes,
                timestamps=timestamps
            )
            
        except Exception as e:
            logger.error(f"Error retrieving market data: {e}")
            return None
    
    def delete_old_data(self, before_date: datetime) -> int:
        """Delete price data older than specified date"""
        try:
            query = self.collection.where('timestamp', '<', before_date)
            docs = query.stream()
            
            batch = self.db.batch()
            deleted_count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                deleted_count += 1
                
                # Firestore batches are limited to 500 operations
                if deleted_count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            if deleted_count % 500 != 0:
                batch.commit()
            
            logger.info(f"Deleted {deleted_count} old price data records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting old data: {e}")
            return 0
    
    def get_symbols(self) -> List[str]:
        """Get list of all symbols in the repository"""
        try:
            # Firestore doesn't support DISTINCT queries directly
            # We'll get all documents and extract unique symbols
            docs = self.collection.stream()
            symbols = set()
            
            for doc in docs:
                data = doc.to_dict()
                symbols.add(data['symbol'])
            
            return sorted(list(symbols))
            
        except Exception as e:
            logger.error(f"Error retrieving symbols: {e}")
            return []
    
    def get_data_statistics(self, symbol: str) -> Dict[str, Any]:
        """Get statistics about stored data for a symbol"""
        try:
            query = self.collection.where('symbol', '==', symbol)
            docs = list(query.stream())
            
            if not docs:
                return {'symbol': symbol, 'total_records': 0}
            
            prices = [doc.to_dict()['price'] for doc in docs]
            timestamps = [doc.to_dict()['timestamp'] for doc in docs]
            
            return {
                'symbol': symbol,
                'total_records': len(docs),
                'date_range': {
                    'start': min(timestamps),
                    'end': max(timestamps)
                },
                'price_stats': {
                    'min': min(prices),
                    'max': max(prices),
                    'average': sum(prices) / len(prices)
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving data statistics: {e}")
            return {}


class FirestoreTradeRepository(TradeRepository):
    """Firestore implementation of trade repository"""
    
    def __init__(self, project_id: Optional[str] = None, collection_name: str = "trades"):
        if not FIRESTORE_AVAILABLE:
            raise ImportError("Firestore not available. Install with: pip install google-cloud-firestore")
        
        self.db = firestore.Client(project=project_id)
        self.collection_name = collection_name
        self.collection: CollectionReference = self.db.collection(collection_name)
        
        logger.info(f"Firestore trade repository initialized for project: {project_id or 'default'}")
    
    def save_trade(self, trade: Trade) -> bool:
        """Save a trade"""
        try:
            # Use trade ID if available, otherwise generate one
            trade_id = trade.id if hasattr(trade, 'id') and trade.id else str(uuid.uuid4())
            
            doc_ref = self.collection.document(trade_id)
            doc_ref.set({
                'symbol': trade.coin.symbol,
                'action': trade.action,
                'amount': trade.amount,
                'price': trade.price,
                'timestamp': trade.timestamp,
                'strategy': trade.strategy,
                'status': 'PENDING',
                'created_at': firestore.SERVER_TIMESTAMP
            })
            
            # Set the ID on the trade object
            trade.id = trade_id
            
            logger.info(f"Saved trade {trade_id} for {trade.coin.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving trade: {e}")
            return False
    
    def get_trades(self, symbol: Optional[str] = None, start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None, limit: Optional[int] = None) -> List[Trade]:
        """Retrieve trades with optional filters"""
        try:
            query = self.collection
            
            if symbol:
                query = query.where('symbol', '==', symbol)
            
            if start_time:
                query = query.where('timestamp', '>=', start_time)
            
            if end_time:
                query = query.where('timestamp', '<=', end_time)
            
            query = query.order_by('timestamp', direction=firestore.Query.DESCENDING)
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            
            trades = []
            for doc in docs:
                data = doc.to_dict()
                coin = Coin(symbol=data['symbol'], name=data['symbol'], precision=8)
                
                trade = Trade(
                    coin=coin,
                    action=data['action'],
                    amount=data['amount'],
                    price=data['price'],
                    timestamp=data['timestamp'],
                    strategy=data['strategy']
                )
                trade.id = doc.id
                trades.append(trade)
            
            return trades
            
        except Exception as e:
            logger.error(f"Error retrieving trades: {e}")
            return []
    
    def get_trade_by_id(self, trade_id: str) -> Optional[Trade]:
        """Get a specific trade by ID"""
        try:
            doc_ref = self.collection.document(trade_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                coin = Coin(symbol=data['symbol'], name=data['symbol'], precision=8)
                
                trade = Trade(
                    coin=coin,
                    action=data['action'],
                    amount=data['amount'],
                    price=data['price'],
                    timestamp=data['timestamp'],
                    strategy=data['strategy']
                )
                trade.id = doc.id
                return trade
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving trade by ID: {e}")
            return None
    
    def update_trade_status(self, trade_id: str, status: str) -> bool:
        """Update trade status"""
        try:
            doc_ref = self.collection.document(trade_id)
            doc_ref.update({
                'status': status,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"Updated trade {trade_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating trade status: {e}")
            return False
    
    def get_trading_statistics(self, symbol: Optional[str] = None, 
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get trading statistics"""
        try:
            trades = self.get_trades(symbol=symbol, start_time=start_time, end_time=end_time)
            
            stats = {
                'total_trades': len(trades),
                'buy_trades': 0,
                'sell_trades': 0,
                'total_volume': 0.0,
                'buy_volume': 0.0,
                'sell_volume': 0.0
            }
            
            for trade in trades:
                volume = trade.amount * trade.price
                stats['total_volume'] += volume
                
                if trade.action == 'BUY':
                    stats['buy_trades'] += 1
                    stats['buy_volume'] += volume
                elif trade.action == 'SELL':
                    stats['sell_trades'] += 1
                    stats['sell_volume'] += volume
            
            return stats
            
        except Exception as e:
            logger.error(f"Error retrieving trading statistics: {e}")
            return {} 