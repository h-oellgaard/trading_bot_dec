import sqlite3
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json

from ..domain.repository import (
    PriceDataRepository, TradeRepository, PriceData, MarketData
)
from ..domain.trade import Trade
from ..domain.coin import Coin


logger = logging.getLogger(__name__)


class SQLitePriceDataRepository(PriceDataRepository):
    """SQLite implementation of price data repository"""
    
    def __init__(self, db_path: str = "trading_bot.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create price_data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS price_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        price REAL NOT NULL,
                        volume REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        source TEXT DEFAULT 'coingecko',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, timestamp)
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_price_data_symbol_timestamp 
                    ON price_data(symbol, timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_price_data_timestamp 
                    ON price_data(timestamp)
                """)
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def save_price_data(self, price_data: PriceData) -> bool:
        """Save a single price data point"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO price_data (symbol, price, volume, timestamp, source)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    price_data.symbol,
                    price_data.price,
                    price_data.volume,
                    price_data.timestamp.isoformat(),
                    price_data.source
                ))
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error saving price data: {e}")
            return False
    
    def save_batch_price_data(self, price_data_list: List[PriceData]) -> bool:
        """Save multiple price data points in batch"""
        if not price_data_list:
            return True
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany("""
                    INSERT OR REPLACE INTO price_data (symbol, price, volume, timestamp, source)
                    VALUES (?, ?, ?, ?, ?)
                """, [
                    (
                        pd.symbol,
                        pd.price,
                        pd.volume,
                        pd.timestamp.isoformat(),
                        pd.source
                    ) for pd in price_data_list
                ])
                conn.commit()
                logger.info(f"Saved {len(price_data_list)} price data points in batch")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error saving batch price data: {e}")
            return False
    
    def get_price_data(self, symbol: str, start_time: Optional[datetime] = None, 
                      end_time: Optional[datetime] = None, limit: Optional[int] = None) -> List[PriceData]:
        """Retrieve price data for a symbol within a time range"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT symbol, price, volume, timestamp, source FROM price_data WHERE symbol = ?"
                params = [symbol]
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time.isoformat())
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time.isoformat())
                
                query += " ORDER BY timestamp ASC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [
                    PriceData(
                        symbol=row[0],
                        price=row[1],
                        volume=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        source=row[4]
                    ) for row in rows
                ]
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving price data: {e}")
            return []
    
    def get_latest_price(self, symbol: str) -> Optional[PriceData]:
        """Get the most recent price data for a symbol"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT symbol, price, volume, timestamp, source 
                    FROM price_data 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, (symbol,))
                
                row = cursor.fetchone()
                if row:
                    return PriceData(
                        symbol=row[0],
                        price=row[1],
                        volume=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        source=row[4]
                    )
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving latest price: {e}")
            return None
    
    def get_market_data(self, symbol: str, periods: int) -> Optional[MarketData]:
        """Get market data for a symbol with specified number of periods"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT price, volume, timestamp 
                    FROM price_data 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (symbol, periods))
                
                rows = cursor.fetchall()
                if not rows:
                    return None
                
                # Reverse to get chronological order
                rows.reverse()
                
                prices = [row[0] for row in rows]
                volumes = [row[1] for row in rows]
                timestamps = [datetime.fromisoformat(row[2]) for row in rows]
                
                return MarketData(
                    symbol=symbol,
                    prices=prices,
                    volumes=volumes,
                    timestamps=timestamps
                )
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving market data: {e}")
            return None
    
    def delete_old_data(self, before_date: datetime) -> int:
        """Delete price data older than specified date"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM price_data WHERE timestamp < ?
                """, (before_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"Deleted {deleted_count} old price data records")
                return deleted_count
                
        except sqlite3.Error as e:
            logger.error(f"Error deleting old data: {e}")
            return 0
    
    def get_symbols(self) -> List[str]:
        """Get list of all symbols in the repository"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT symbol FROM price_data ORDER BY symbol")
                return [row[0] for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving symbols: {e}")
            return []
    
    def get_data_statistics(self, symbol: str) -> Dict[str, Any]:
        """Get statistics about stored data for a symbol"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total count
                cursor.execute("SELECT COUNT(*) FROM price_data WHERE symbol = ?", (symbol,))
                total_count = cursor.fetchone()[0]
                
                # Get date range
                cursor.execute("""
                    SELECT MIN(timestamp), MAX(timestamp) 
                    FROM price_data WHERE symbol = ?
                """, (symbol,))
                min_date, max_date = cursor.fetchone()
                
                # Get price statistics
                cursor.execute("""
                    SELECT MIN(price), MAX(price), AVG(price) 
                    FROM price_data WHERE symbol = ?
                """, (symbol,))
                min_price, max_price, avg_price = cursor.fetchone()
                
                return {
                    'symbol': symbol,
                    'total_records': total_count,
                    'date_range': {
                        'start': min_date,
                        'end': max_date
                    },
                    'price_stats': {
                        'min': min_price,
                        'max': max_price,
                        'average': avg_price
                    }
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving data statistics: {e}")
            return {}


class SQLiteTradeRepository(TradeRepository):
    """SQLite implementation of trade repository"""
    
    def __init__(self, db_path: str = "trading_bot.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with trade table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create trades table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id TEXT PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        action TEXT NOT NULL,
                        amount REAL NOT NULL,
                        price REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        strategy TEXT NOT NULL,
                        status TEXT DEFAULT 'PENDING',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp 
                    ON trades(symbol, timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_trades_status 
                    ON trades(status)
                """)
                
                conn.commit()
                logger.info("Trade database initialized")
                
        except sqlite3.Error as e:
            logger.error(f"Trade database initialization error: {e}")
            raise
    
    def save_trade(self, trade: Trade) -> bool:
        """Save a trade"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO trades (id, symbol, action, amount, price, timestamp, strategy, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade.id,
                    trade.coin.symbol,
                    trade.action,
                    trade.amount,
                    trade.price,
                    trade.timestamp.isoformat(),
                    trade.strategy,
                    'PENDING'
                ))
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error saving trade: {e}")
            return False
    
    def get_trades(self, symbol: Optional[str] = None, start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None, limit: Optional[int] = None) -> List[Trade]:
        """Retrieve trades with optional filters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT id, symbol, action, amount, price, timestamp, strategy, status FROM trades WHERE 1=1"
                params = []
                
                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time.isoformat())
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time.isoformat())
                
                query += " ORDER BY timestamp DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                trades = []
                for row in rows:
                    coin = Coin(symbol=row[1], name=row[1], precision=8)  # Default precision
                    trade = Trade(
                        coin=coin,
                        action=row[2],
                        amount=row[3],
                        price=row[4],
                        timestamp=datetime.fromisoformat(row[5]),
                        strategy=row[6]
                    )
                    trade.id = row[0]  # Set the ID from database
                    trades.append(trade)
                
                return trades
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving trades: {e}")
            return []
    
    def get_trade_by_id(self, trade_id: str) -> Optional[Trade]:
        """Get a specific trade by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, symbol, action, amount, price, timestamp, strategy, status 
                    FROM trades WHERE id = ?
                """, (trade_id,))
                
                row = cursor.fetchone()
                if row:
                    coin = Coin(symbol=row[1], name=row[1], precision=8)
                    trade = Trade(
                        coin=coin,
                        action=row[2],
                        amount=row[3],
                        price=row[4],
                        timestamp=datetime.fromisoformat(row[5]),
                        strategy=row[6]
                    )
                    trade.id = row[0]
                    return trade
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving trade by ID: {e}")
            return None
    
    def update_trade_status(self, trade_id: str, status: str) -> bool:
        """Update trade status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE trades SET status = ? WHERE id = ?
                """, (status, trade_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Error updating trade status: {e}")
            return False
    
    def get_trading_statistics(self, symbol: Optional[str] = None, 
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get trading statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT action, COUNT(*), SUM(amount * price) FROM trades WHERE 1=1"
                params = []
                
                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time.isoformat())
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time.isoformat())
                
                query += " GROUP BY action"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                stats = {
                    'total_trades': 0,
                    'buy_trades': 0,
                    'sell_trades': 0,
                    'total_volume': 0.0,
                    'buy_volume': 0.0,
                    'sell_volume': 0.0
                }
                
                for row in rows:
                    action, count, volume = row
                    stats['total_trades'] += count
                    stats['total_volume'] += volume or 0
                    
                    if action == 'BUY':
                        stats['buy_trades'] = count
                        stats['buy_volume'] = volume or 0
                    elif action == 'SELL':
                        stats['sell_trades'] = count
                        stats['sell_volume'] = volume or 0
                
                return stats
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving trading statistics: {e}")
            return {} 