"""
Main trading bot orchestrator.
Runs continuous loop to fetch data, generate signals, and execute trades.
"""
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

from data_fetcher import FiriDataFetcher
from strategy import TradingStrategy
from trader import FiriTrader
from firebase_store import FirebaseStore, FirebaseLoggingHandler
from models import Trade, TradeStatus, Signal, SignalType, PortfolioState, Candle

load_dotenv()

# Configure logging (Firebase handler added in TradingBot.__init__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TradingBot:
    """Main trading bot orchestrator."""
    
    def __init__(self):
        """Initialize trading bot with all components."""
        self.pair = os.getenv("TRADING_PAIR", "BTC/DKK")
        self.poll_interval = int(os.getenv("POLL_INTERVAL", "30"))  # Default 30 seconds
        self.trailing_stop_loss_percent = float(os.getenv("TRAILING_STOP_LOSS_PERCENT", "7.0"))
        self.cooldown_candles = int(os.getenv("COOLDOWN_CANDLES", "25"))
        
        # Initialize components
        self.data_fetcher = FiriDataFetcher()
        self.strategy = TradingStrategy(
            short_ema_period=int(os.getenv("SHORT_EMA_PERIOD", "10")),
            medium_ema_period=int(os.getenv("MEDIUM_EMA_PERIOD", "20")),
            long_ema_period=int(os.getenv("LONG_EMA_PERIOD", "50"))
        )
        self.trader = FiriTrader()
        self.firebase = FirebaseStore()

        # Add Firebase logging handler
        firebase_handler = FirebaseLoggingHandler(self.firebase)
        firebase_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(firebase_handler)

        logger.info(f"Trading bot initialized for pair: {self.pair}")
        logger.info(f"EMA periods: Short={self.strategy.short_ema_period}, "
                   f"Medium={self.strategy.medium_ema_period}, "
                   f"Long={self.strategy.long_ema_period}")
        logger.info(f"Poll interval: {self.poll_interval} seconds")
        logger.info(f"Trailing stop loss: {self.trailing_stop_loss_percent}%")
        logger.info(f"Cooldown: {self.cooldown_candles} candles")
    
    def initialize(self) -> None:
        """Initialize and load initial data (100 candles with 30-minute intervals) at startup."""
        logger.info("Loading initial candle data (100 candles with 30-minute intervals)...")
        
        # First, try to get candles from Firebase
        try:
            firebase_candles = self.firebase.get_price_snapshots(pair=self.pair, limit=100)
            if firebase_candles and len(firebase_candles) >= 50:  # If we have at least 50 candles in Firebase
                logger.info(f"Found {len(firebase_candles)} candles in Firebase")
                # Still fetch from API to get latest data, but we have historical data
                logger.info("Fetching latest candles from API to update data...")
                api_candles = self.data_fetcher.get_candles(
                    pair=self.pair,
                    interval="30m",
                    limit=100
                )
                if api_candles:
                    logger.info(f"Successfully loaded {len(api_candles)} candles from API")
                    # Save all candles to Firebase
                    for candle in api_candles:
                        self.firebase.save_price_snapshot(pair=self.pair, candle=candle)
                    return
            else:
                logger.info(f"Not enough data in Firebase ({len(firebase_candles) if firebase_candles else 0} candles), fetching from API...")
        except Exception as e:
            logger.warning(f"Error loading from Firebase: {e}, fetching from API instead...")
        
        # If not enough data in Firebase, fetch from API
        try:
            candles = self.data_fetcher.get_candles(
                pair=self.pair,
                interval="30m",
                limit=100
            )
            if candles:
                logger.info(f"Successfully loaded {len(candles)} candles from API at startup")
                # Save all candles to Firebase
                for candle in candles:
                    self.firebase.save_price_snapshot(pair=self.pair, candle=candle)
            else:
                logger.warning("No candles loaded at startup")
        except Exception as e:
            logger.error(f"Error loading initial candles from API: {e}", exc_info=True)
            raise
    
    def get_open_trade(self) -> Optional[Trade]:
        """Get the current open trade if any."""
        open_trades = self.firebase.get_open_trades(pair=self.pair)
        if open_trades:
            return open_trades[0]  # Should only have one open trade
        return None
    
    def is_in_cooldown(self) -> bool:
        """Check if we're in cooldown period after a sell."""
        # Get the most recent closed trade
        recent_trades = self.firebase.get_recent_trades(pair=self.pair, limit=1)
        if not recent_trades:
            return False
        
        last_trade = recent_trades[0]
        if last_trade.status != TradeStatus.CLOSED or last_trade.side != "sell":
            return False
        
        # Get recent candles to check cooldown
        candles = self.data_fetcher.get_candles(
            pair=self.pair,
            interval="30m",
            limit=self.cooldown_candles + 10
        )
        
        if not candles or len(candles) < self.cooldown_candles:
            return False
        
        # Check if last sell was within cooldown period
        if last_trade.close_timestamp:
            time_since_sell = datetime.now() - last_trade.close_timestamp
            # Approximate: 1 candle = 1 hour
            candles_since_sell = int(time_since_sell.total_seconds() / 3600)
            return candles_since_sell < self.cooldown_candles
        
        return False
    
    def check_trailing_stop_loss(self, trade: Trade, current_price: float) -> bool:
        """Check if trailing stop loss should trigger."""
        should_trigger, new_highest = self.strategy.should_trailing_stop_loss(
            entry_price=trade.price,
            current_price=current_price,
            highest_price=trade.highest_price or trade.price,
            trailing_stop_percent=self.trailing_stop_loss_percent
        )
        
        # Update highest price in trade
        if new_highest > (trade.highest_price or trade.price):
            trade.highest_price = new_highest
            self.firebase.save_trade(trade)
        
        return should_trigger
    
    def close_trade(self, trade: Trade, reason: str) -> None:
        """Close an open trade by placing a sell order."""
        logger.info(f"Closing trade {trade.trade_id}: {reason}")
        
        try:
            # Get current price for sell order
            current_price = self.data_fetcher.get_current_price(trade.pair)
            if current_price is None:
                logger.error(f"Could not get current price for {trade.pair}")
                return
            
            # Place sell order
            sell_trade = self.trader.place_sell_order(
                pair=trade.pair,
                quantity=trade.quantity,
                price=current_price
            )
            
            # Get actual executed price
            close_price = sell_trade.price
            close_timestamp = datetime.now()
            
            # Calculate profit/loss
            profit_loss = (close_price - trade.price) * trade.quantity
            profit_loss_percent = ((close_price - trade.price) / trade.price) * 100
            
            # Update trade
            trade.status = TradeStatus.CLOSED
            trade.close_price = close_price
            trade.close_timestamp = close_timestamp
            trade.profit_loss = profit_loss
            trade.profit_loss_percent = profit_loss_percent
            
            # Save to Firebase
            self.firebase.save_trade(trade)
            
            logger.info(f"Trade closed: P/L = {profit_loss:.2f} DKK ({profit_loss_percent:.2f}%)")
            
        except Exception as e:
            logger.error(f"Error closing trade: {e}", exc_info=True)
    
    def execute_buy_signal(self, signal: Signal, current_price: float) -> None:
        """Execute a BUY signal by placing a buy order."""
        logger.info(f"Executing BUY signal: {signal.reason}")
        
        try:
            # Get balance
            quote_currency = self.pair.split('/')[1]  # e.g., "DKK"
            balance = self.trader.get_balance(currency=quote_currency)
            
            if balance <= 0:
                logger.warning(f"Insufficient balance: {balance} {quote_currency}")
                return
            
            # Calculate quantity (use 95% of balance to leave some margin)
            quantity = (balance * 0.95) / current_price
            
            # Place buy order
            trade = self.trader.place_buy_order(
                pair=self.pair,
                quantity=quantity,
                price=current_price
            )
            
            # Initialize highest price for trailing stop
            trade.highest_price = current_price
            
            # Save to Firebase
            self.firebase.save_trade(trade)
            
            logger.info(f"Buy order placed: {quantity:.8f} {self.pair.split('/')[0]} at {current_price:.2f} {quote_currency}")
            
        except Exception as e:
            logger.error(f"Error executing buy signal: {e}", exc_info=True)
    
    def update_portfolio_state(self) -> None:
        """Update and save portfolio state to Firebase."""
        try:
            # Get balances
            base_currency = self.pair.split('/')[0]  # e.g., "BTC"
            quote_currency = self.pair.split('/')[1]  # e.g., "DKK"
            
            balance_btc = self.trader.get_balance(currency=base_currency)
            balance_nok = self.trader.get_balance(currency=quote_currency)
            
            # Get current price
            current_price = self.data_fetcher.get_current_price(self.pair)
            if current_price is None:
                logger.warning("Could not get current price for portfolio calculation")
                return
            
            # Calculate total value
            total_value_nok = balance_nok + (balance_btc * current_price)
            
            # Get trade statistics
            open_trades = self.firebase.get_open_trades(pair=self.pair)
            closed_trades = self.firebase.get_closed_trades(pair=self.pair)
            
            # Calculate total profit/loss from closed trades
            total_profit_loss = sum(
                trade.profit_loss or 0 
                for trade in closed_trades 
                if trade.profit_loss is not None
            )
            
            # Calculate profit/loss percentage
            total_profit_loss_percent = 0.0
            if closed_trades:
                total_invested = sum(trade.price * trade.quantity for trade in closed_trades)
                if total_invested > 0:
                    total_profit_loss_percent = (total_profit_loss / total_invested) * 100
            
            # Create portfolio state
            portfolio = PortfolioState(
                timestamp=datetime.now(),
                balance_nok=balance_nok,
                balance_btc=balance_btc,
                total_value_nok=total_value_nok,
                open_trades_count=len(open_trades),
                closed_trades_count=len(closed_trades),
                total_profit_loss=total_profit_loss,
                total_profit_loss_percent=total_profit_loss_percent
            )
            
            # Save to Firebase
            self.firebase.save_portfolio_state(portfolio)
            
            logger.info(f"Portfolio updated: Total value = {total_value_nok:.2f} {quote_currency}, "
                       f"P/L = {total_profit_loss:.2f} {quote_currency} ({total_profit_loss_percent:.2f}%)")
            
        except Exception as e:
            logger.error(f"Error updating portfolio state: {e}", exc_info=True)
    
    def save_price_snapshot(self, candles: list[Candle]) -> None:
        """Save latest price to Firebase prices collection each interval."""
        # Use ticker (order book) for live price - updates even without trades
        current_price = self.data_fetcher.get_ticker_price(self.pair)
        if current_price is None and candles:
            current_price = candles[-1].close
        if current_price is None:
            return

        now = datetime.now()

        try:
            snapshot = Candle(
                timestamp=now,
                open=current_price,
                high=current_price,
                low=current_price,
                close=current_price,
                volume=0.0
            )
            self.firebase.save_price_snapshot(
                pair=self.pair,
                candle=snapshot
            )
        except Exception as e:
            logger.error(f"Error saving price snapshot: {e}", exc_info=True)
    
    def run_iteration(self) -> None:
        """Run one iteration of the trading bot."""
        logger.info("=" * 60)
        logger.info("Starting trading bot iteration")
        
        try:
            # Fetch candles (load 100 candles for better historical data)
            candles = self.data_fetcher.get_candles(
                pair=self.pair,
                interval="30m",
                limit=100
            )
            
            if not candles or len(candles) < self.strategy.long_ema_period:
                logger.warning(f"Insufficient candles: {len(candles) if candles else 0} < {self.strategy.long_ema_period}")
                return
            
            # Save price snapshot
            self.save_price_snapshot(candles)
            
            # Get current price
            current_price = candles[-1].close
            
            # Get open trade
            open_trade = self.get_open_trade()
            
            # Check trailing stop loss if we have an open trade
            if open_trade:
                if self.check_trailing_stop_loss(open_trade, current_price):
                    self.close_trade(open_trade, "Trailing stop loss triggered")
                    open_trade = None  # Trade is now closed
            
            # Check cooldown
            in_cooldown = self.is_in_cooldown()
            
            # Generate signal
            signal = self.strategy.generate_signal(
                candles=candles,
                has_open_trade=open_trade is not None,
                in_cooldown=in_cooldown
            )
            
            # Save signal to Firebase
            self.firebase.save_signal(signal)
            
            logger.info(f"Signal generated: {signal.signal_type.value.upper()} - {signal.reason}")
            if signal.short_ema:
                logger.info(f"  Short EMA: {signal.short_ema:.2f}")
            if signal.medium_ema:
                logger.info(f"  Medium EMA: {signal.medium_ema:.2f}")
            if signal.long_ema:
                logger.info(f"  Long EMA: {signal.long_ema:.2f}")
            
            # Execute signal
            if signal.signal_type == SignalType.BUY and not open_trade:
                self.execute_buy_signal(signal, current_price)
            elif signal.signal_type == SignalType.SELL and open_trade:
                self.close_trade(open_trade, signal.reason)
            
            # Update portfolio state
            self.update_portfolio_state()
            
            logger.info("Trading bot iteration completed")
            
        except Exception as e:
            logger.error(f"Error in trading bot iteration: {e}", exc_info=True)
    
    def run(self) -> None:
        """Run the trading bot continuously."""
        logger.info("Starting trading bot...")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_iteration()
                logger.info(f"Waiting {self.poll_interval} seconds until next iteration...")
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logger.info("Trading bot stopped by user")
        except Exception as e:
            logger.error(f"Fatal error in trading bot: {e}", exc_info=True)
            raise


def main():
    """Main entry point."""
    bot = TradingBot()
    bot.initialize()  # Load initial data (100 candles)
    bot.run()


if __name__ == "__main__":
    main()
