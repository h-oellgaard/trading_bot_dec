"""
Firebase Firestore storage module.
Pure data storage layer with no business logic.
"""
import json
import logging
import os
import traceback
from datetime import datetime
from typing import Optional, List
from google.cloud import firestore
from google.oauth2 import service_account
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

    MAX_SERIES_ENTRIES_PER_PAIR = int(os.getenv("MAX_SERIES_ENTRIES_PER_PAIR", "150"))

    def __init__(self):
        # Support both JSON env var (Render/cloud) and file path (local)
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON", "").strip()
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()

        if credentials_json:
            # Render/cloud: credentials as JSON string in env var
            try:
                info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(info)
                project = info.get("project_id")
                if not project:
                    raise ValueError("Service account JSON missing 'project_id'")
                self.db = firestore.Client(credentials=credentials, project=project)
            except json.JSONDecodeError as e:
                raise ValueError(f"GOOGLE_APPLICATION_CREDENTIALS_JSON is invalid JSON: {e}")
        elif credentials_path:
            # Local: credentials from file path (file must exist)
            if not os.path.isfile(credentials_path):
                raise ValueError(
                    f"Firebase credentials file not found: {credentials_path}\n"
                    "On Render: set GOOGLE_APPLICATION_CREDENTIALS_JSON with the full JSON content instead."
                )
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            self.db = firestore.Client()
        else:
            raise ValueError(
                "Set GOOGLE_APPLICATION_CREDENTIALS_JSON (full JSON string) for Render, "
                "or GOOGLE_APPLICATION_CREDENTIALS (file path) for local dev"
            )
    
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

    def save_ema_values(
        self,
        pair: str,
        timestamp: datetime,
        short_ema: Optional[float],
        medium_ema: Optional[float],
        long_ema: Optional[float],
    ) -> None:
        """
        Save EMA values to ema_short, ema_medium, ema_long collections.
        Each document has timestamp, value, and pair.
        """
        doc_id = f"{pair.replace('/', '_')}_{timestamp.isoformat()}"
        base_data = {"timestamp": timestamp.isoformat(), "pair": pair}

        if short_ema is not None:
            self.db.collection("ema_short").document(doc_id).set(
                {**base_data, "value": short_ema}
            )
            self._trim_collection_for_pair(
                "ema_short",
                pair,
                self.MAX_SERIES_ENTRIES_PER_PAIR,
            )
        if medium_ema is not None:
            self.db.collection("ema_medium").document(doc_id).set(
                {**base_data, "value": medium_ema}
            )
            self._trim_collection_for_pair(
                "ema_medium",
                pair,
                self.MAX_SERIES_ENTRIES_PER_PAIR,
            )
        if long_ema is not None:
            self.db.collection("ema_long").document(doc_id).set(
                {**base_data, "value": long_ema}
            )
            self._trim_collection_for_pair(
                "ema_long",
                pair,
                self.MAX_SERIES_ENTRIES_PER_PAIR,
            )

    def clear_ema_for_pair(self, pair: str) -> None:
        """Delete all EMA documents for a trading pair (short, medium, long)."""
        for coll in ("ema_short", "ema_medium", "ema_long"):
            query = self.db.collection(coll).where(
                filter=firestore.FieldFilter("pair", "==", pair)
            )
            batch = self.db.batch()
            n = 0
            for doc in query.stream():
                batch.delete(doc.reference)
                n += 1
                if n % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            if n % 500 != 0 and n > 0:
                batch.commit()
        logging.getLogger(__name__).debug(f"Cleared EMA data for {pair}")

    def get_ema_history(
        self,
        collection: str,
        pair: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        """
        Get EMA history from ema_short, ema_medium, or ema_long collection.

        Args:
            collection: "ema_short", "ema_medium", or "ema_long"
            pair: Optional pair filter (e.g., "ETH/DKK")
            limit: Max documents to return

        Returns:
            List of dicts with timestamp, value, pair
        """
        if pair:
            return [
                doc.to_dict()
                for doc in self._pair_docs_newest_first(collection, pair)[:limit]
            ]
        query = (
            self.db.collection(collection)
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        return [doc.to_dict() for doc in query.stream()]
    
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
        self._trim_collection_for_pair(
            "prices",
            pair,
            self.MAX_SERIES_ENTRIES_PER_PAIR,
        )

    def _pair_docs_newest_first(self, collection: str, pair: str) -> List:
        """
        Load all documents for a pair and sort by timestamp descending.

        Uses an equality filter only on ``pair`` (automatic single-field index),
        then sorts in memory. Firestore requires a composite index for
        ``where(pair)`` + ``order_by(timestamp)`` on the server, which we avoid.
        """
        query = self.db.collection(collection).where(
            filter=firestore.FieldFilter("pair", "==", pair)
        )
        docs = list(query.stream())

        def doc_timestamp_key(doc) -> str:
            data = doc.to_dict() or {}
            t = data.get("timestamp")
            return t if isinstance(t, str) else ""

        docs.sort(key=doc_timestamp_key, reverse=True)
        return docs

    def _trim_collection_for_pair(self, collection: str, pair: str, keep: int) -> None:
        """
        Keep only the newest `keep` docs for a pair in one collection.
        Deletes older documents in Firestore batches.
        """
        if keep <= 0:
            return

        batch = self.db.batch()
        to_delete = 0
        for index, doc in enumerate(self._pair_docs_newest_first(collection, pair)):
            if index < keep:
                continue
            batch.delete(doc.reference)
            to_delete += 1
            if to_delete % 500 == 0:
                batch.commit()
                batch = self.db.batch()

        if to_delete % 500 != 0 and to_delete > 0:
            batch.commit()
    
    def clear_prices_for_other_pairs(self, keep_pair: str) -> None:
        """
        Delete price snapshots for all pairs except keep_pair.
        Prevents mixing when multiple bot instances or old config runs.
        """
        query = self.db.collection("prices")
        batch = self.db.batch()
        count = 0
        for doc in query.stream():
            data = doc.to_dict()
            if data.get("pair") != keep_pair:
                batch.delete(doc.reference)
                count += 1
                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
        if count % 500 != 0 and count > 0:
            batch.commit()
        if count > 0:
            logging.getLogger(__name__).info(f"Cleared {count} price snapshots for other pairs (keeping {keep_pair})")

    def clear_prices_for_pair(self, pair: str) -> None:
        """
        Delete all price snapshots for a trading pair.
        Used at startup to replace with fresh API data.
        """
        query = self.db.collection("prices").where(
            filter=firestore.FieldFilter("pair", "==", pair)
        )
        BATCH_SIZE = 500  # Firestore batch limit
        batch = self.db.batch()
        count = 0
        for doc in query.stream():
            batch.delete(doc.reference)
            count += 1
            if count % BATCH_SIZE == 0:
                batch.commit()
                batch = self.db.batch()
        if count > 0:
            if count % BATCH_SIZE != 0:
                batch.commit()
            logging.getLogger(__name__).info(f"Cleared {count} price snapshots for {pair}")

    def clear_all_prices(self) -> None:
        """
        Delete all price snapshots. Used at startup when switching pairs
        to avoid mixing different pairs (e.g., ETH/DKK and ETH/NOK) in the dashboard.
        """
        query = self.db.collection("prices")
        BATCH_SIZE = 500  # Firestore batch limit
        batch = self.db.batch()
        count = 0
        for doc in query.stream():
            batch.delete(doc.reference)
            count += 1
            if count % BATCH_SIZE == 0:
                batch.commit()
                batch = self.db.batch()
        if count > 0:
            if count % BATCH_SIZE != 0:
                batch.commit()
            logging.getLogger(__name__).info(f"Cleared all {count} price snapshots")

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
        for doc in self._pair_docs_newest_first("prices", pair)[:limit]:
            candles.append(Candle.from_dict(doc.to_dict()))

        # Return in chronological order (oldest first)
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

