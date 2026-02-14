"""
Firebase Firestore storage module.
Pure data storage layer with no business logic.
"""
import logging
import os
import traceback
from datetime import datetime
from typing import Optional, List
from google.cloud import firestore
from dotenv import load_dotenv

from models import Trade, Signal, PortfolioState, Candle

load_dotenv()


class FirebaseLoggingHandler(logging.Handler):
    """Logging handler that writes log records to Firebase Firestore."""

    def __init__(self, firebase_store: "FirebaseStore"):
        super().__init__()
        self.firebase_store = firebase_store

    def emit(self, record: logging.LogRecord) -> None:
        try:
            exc_info = None
            if record.exc_info:
                exc_info = "".join(traceback.format_exception(*record.exc_info))

            self.firebase_store.save_log(
                level=record.levelname,
                logger_name=record.name,
                message=self.format(record),
                exc_info=exc_info,
            )
        except Exception:
            # Avoid infinite loop - never let logging failures propagate
            self.handleError(record)


class FirebaseStore:
    """Handles all data storage in Firebase Firestore."""
    
    def __init__(self):
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS must be set in .env")
        
        # Initialize Firestore client
        # The client will use the service account credentials from the path
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        self.db = firestore.Client()
    
    def save_trade(self, trade: Trade) -> None:
        """
        Save a trade to Firestore.
        
        Args:
            trade: Trade object to save
        """
        trade_ref = self.db.collection("trades").document(trade.trade_id)
        trade_ref.set(trade.to_dict())
    
    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """
        Get a trade by ID.
        
        Args:
            trade_id: Trade ID
            
        Returns:
            Trade object or None if not found
        """
        trade_ref = self.db.collection("trades").document(trade_id)
        trade_doc = trade_ref.get()
        
        if not trade_doc.exists:
            return None
        
        return Trade.from_dict(trade_doc.to_dict())
    
    def get_open_trades(self, pair: Optional[str] = None) -> List[Trade]:
        """
        Get all open trades.
        
        Args:
            pair: Optional trading pair to filter by
            
        Returns:
            List of open Trade objects
        """
        query = self.db.collection("trades").where(filter=firestore.FieldFilter("status", "==", "open"))
        
        if pair:
            query = query.where(filter=firestore.FieldFilter("pair", "==", pair))
        
        trades = []
        for doc in query.stream():
            trades.append(Trade.from_dict(doc.to_dict()))
        
        return trades
    
    def update_trade(self, trade: Trade) -> None:
        """
        Update an existing trade.
        
        Args:
            trade: Trade object with updated data
        """
        trade_ref = self.db.collection("trades").document(trade.trade_id)
        # Use set with merge=True to handle both create and update cases
        trade_ref.set(trade.to_dict(), merge=True)
    
    def save_signal(self, signal: Signal) -> None:
        """
        Save a trading signal to Firestore.
        
        Args:
            signal: Signal object to save
        """
        # Use signal_id as document ID to avoid collisions
        # If multiple signals generated at same timestamp, they'll have different IDs
        signal_ref = self.db.collection("signals").document(signal.signal_id)
        signal_ref.set(signal.to_dict())
    
    def get_recent_signals(self, limit: int = 100) -> List[Signal]:
        """
        Get recent trading signals.
        
        Args:
            limit: Maximum number of signals to retrieve
            
        Returns:
            List of Signal objects
        """
        signals = []
        query = self.db.collection("signals").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        
        for doc in query.stream():
            signals.append(Signal.from_dict(doc.to_dict()))
        
        return signals
    
    def save_portfolio_state(self, portfolio: PortfolioState) -> None:
        """
        Save portfolio state to Firestore.
        
        Args:
            portfolio: PortfolioState object to save
        """
        # Store current state in portfolio/current
        portfolio_ref = self.db.collection("portfolio").document("current")
        portfolio_ref.set(portfolio.to_dict())
        
        # Also save historical snapshot
        timestamp_str = portfolio.timestamp.isoformat()
        history_ref = self.db.collection("portfolio").document("history").collection("snapshots").document(timestamp_str)
        history_ref.set(portfolio.to_dict())
    
    def get_current_portfolio_state(self) -> Optional[PortfolioState]:
        """
        Get current portfolio state.
        
        Returns:
            PortfolioState object or None if not found
        """
        portfolio_ref = self.db.collection("portfolio").document("current")
        portfolio_doc = portfolio_ref.get()
        
        if not portfolio_doc.exists:
            return None
        
        return PortfolioState.from_dict(portfolio_doc.to_dict())
    
    def save_price_snapshot(self, pair: str, candle: Candle) -> None:
        """
        Save a price snapshot to Firestore.
        
        Args:
            pair: Trading pair
            candle: Candle object to save
        """
        # Use timestamp + pair as document ID to avoid collisions
        # This allows same timestamp for different pairs
        timestamp_str = candle.timestamp.isoformat()
        doc_id = f"{pair.replace('/', '_')}_{timestamp_str}"
        snapshot_data = candle.to_dict()
        snapshot_data["pair"] = pair
        
        snapshot_ref = self.db.collection("prices").document(doc_id)
        snapshot_ref.set(snapshot_data)
    
    def get_price_history(self, pair: str, limit: int = 100) -> List[Candle]:
        """
        Get price history for a trading pair.
        
        Args:
            pair: Trading pair
            limit: Maximum number of candles to retrieve
            
        Returns:
            List of Candle objects
        """
        candles = []
        query = self.db.collection("prices").where(filter=firestore.FieldFilter("pair", "==", pair)).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        
        for doc in query.stream():
            data = doc.to_dict()
            candles.append(Candle.from_dict(data))
        
        # Return in chronological order
        candles.reverse()
        return candles
    
    def get_price_snapshots(self, pair: str, limit: int = 100) -> List[Candle]:
        """
        Get price snapshots (candles) from Firestore for a pair.
        Alias for get_price_history for consistency.
        
        Args:
            pair: Trading pair
            limit: Maximum number of candles to retrieve
            
        Returns:
            List of Candle objects sorted by timestamp (oldest first)
        """
        return self.get_price_history(pair, limit)
    
    def get_all_trades(self, pair: Optional[str] = None, limit: int = 1000) -> List[Trade]:
        """
        Get all trades (open and closed).
        
        Args:
            pair: Optional trading pair to filter by
            limit: Maximum number of trades to retrieve
            
        Returns:
            List of Trade objects
        """
        query = self.db.collection("trades")
        
        if pair:
            query = query.where(filter=firestore.FieldFilter("pair", "==", pair))
        
        query = query.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        
        trades = []
        for doc in query.stream():
            trades.append(Trade.from_dict(doc.to_dict()))
        
        return trades
    
    def get_recent_trades(self, pair: Optional[str] = None, limit: int = 10) -> List[Trade]:
        """
        Get recent trades, optionally filtered by pair.
        
        Args:
            pair: Optional trading pair to filter by
            limit: Maximum number of trades to retrieve
            
        Returns:
            List of Trade objects
        """
        return self.get_all_trades(pair=pair, limit=limit)
    
    def get_closed_trades(self, pair: Optional[str] = None) -> List[Trade]:
        """
        Get all closed trades, optionally filtered by pair.
        
        Args:
            pair: Optional trading pair to filter by
            
        Returns:
            List of closed Trade objects
        """
        query = self.db.collection("trades").where(filter=firestore.FieldFilter("status", "==", "closed"))
        
        if pair:
            query = query.where(filter=firestore.FieldFilter("pair", "==", pair))
        
        query = query.order_by("timestamp", direction=firestore.Query.DESCENDING)
        
        trades = []
        for doc in query.stream():
            trades.append(Trade.from_dict(doc.to_dict()))
        
        return trades

    def save_log(self, level: str, logger_name: str, message: str, exc_info: Optional[str] = None) -> None:
        """
        Save a log entry to Firestore.

        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            logger_name: Name of the logger
            message: Log message
            exc_info: Optional exception traceback string
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "logger": logger_name,
            "message": message,
        }
        if exc_info:
            log_data["exc_info"] = exc_info

        # Use auto-generated ID to avoid collisions
        self.db.collection("logs").add(log_data)

