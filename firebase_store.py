"""
Firebase Firestore storage module.
Pure data storage layer with no business logic.
"""
import os
from datetime import datetime
from typing import Optional, List
from google.cloud import firestore
from dotenv import load_dotenv

from models import Trade, Signal, PortfolioState, Candle

load_dotenv()


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
        query = self.db.collection("trades").where("status", "==", "open")
        
        if pair:
            query = query.where("pair", "==", pair)
        
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
        trade_ref.update(trade.to_dict())
    
    def save_signal(self, signal: Signal) -> None:
        """
        Save a trading signal to Firestore.
        
        Args:
            signal: Signal object to save
        """
        # Use timestamp as document ID for easy querying
        timestamp_str = signal.timestamp.isoformat()
        signal_ref = self.db.collection("signals").document(timestamp_str)
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
    
    def save_price_snapshot(self, candle: Candle, pair: str) -> None:
        """
        Save a price snapshot to Firestore.
        
        Args:
            candle: Candle object to save
            pair: Trading pair
        """
        timestamp_str = candle.timestamp.isoformat()
        snapshot_data = candle.to_dict()
        snapshot_data["pair"] = pair
        
        snapshot_ref = self.db.collection("prices").document(timestamp_str)
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
        query = self.db.collection("prices").where("pair", "==", pair).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        
        for doc in query.stream():
            data = doc.to_dict()
            candles.append(Candle.from_dict(data))
        
        # Return in chronological order
        candles.reverse()
        return candles
    
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
            query = query.where("pair", "==", pair)
        
        query = query.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        
        trades = []
        for doc in query.stream():
            trades.append(Trade.from_dict(doc.to_dict()))
        
        return trades

