"""
Main trading bot orchestration module.
Coordinates all components and runs the trading loop.
"""
import os
import time
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from data_fetcher import FiriDataFetcher
from indicators import get_latest_sma, get_latest_ema
from strategy import TradingStrategy
from trader import FiriTrader
from firebase_store import FirebaseStore
from models import Trade, TradeStatus, SignalType, PortfolioState

# Load environment variables
load_dotenv()

# Configure logging
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
        """Initialize all components."""
        self.pair = os.getenv("TRADING_PAIR", "BTC/NOK")
        self.short_sma_period = int(os.getenv("SHORT_SMA_PERIOD", "10"))
        self.long_sma_period = int(os.getenv("LONG_SMA_PERIOD", "30"))
        self.short_ema_period = int(os.getenv("SHORT_EMA_PERIOD", "12"))
        self.long_sma_for_ema = int(os.getenv("LONG_SMA_FOR_EMA", "30"))
        self.take_profit_percent = float(os.getenv("TAKE_PROFIT_PERCENT", "5.0"))
        self.stop_loss_percent = float(os.getenv("STOP_LOSS_PERCENT", "3.0"))
        self.candle_interval = os.getenv("CANDLE_INTERVAL", "1h")
        self.poll_interval = int(os.getenv("POLL_INTERVAL", "300"))  # 5 minutes default
        
        # Initialize components
        self.data_fetcher = FiriDataFetcher()
        self.strategy = TradingStrategy(
            short_sma_period=self.short_sma_period,
            long_sma_period=self.long_sma_period,
            short_ema_period=self.short_ema_period,
            long_sma_for_ema=self.long_sma_for_ema
        )
        self.trader = FiriTrader()
        self.firebase = FirebaseStore()
        
        logger.info("Trading bot initialized")
        logger.info(f"Pair: {self.pair}")
        logger.info(f"Take profit: {self.take_profit_percent}%")
        logger.info(f"Stop loss: {self.stop_loss_percent}%")
    
    def get_open_trade(self) -> Optional[Trade]:
        """Get the current open trade if any."""
        open_trades = self.firebase.get_open_trades(pair=self.pair)
        if open_trades:
            return open_trades[0]  # Max one open trade
        return None
    
    def check_take_profit_stop_loss(self, trade: Trade) -> bool:
        """
        Check if take profit or stop loss should be triggered.
        
        Args:
            trade: Open trade to check
            
        Returns:
            True if trade was closed, False otherwise
        """
        try:
            current_price = self.data_fetcher.get_latest_price(self.pair)
            
            # Check take profit
            if self.strategy.should_take_profit(trade.price, current_price, self.take_profit_percent):
                logger.info(f"Take profit triggered for trade {trade.trade_id}")
                self.close_trade(trade, current_price, "take_profit")
                return True
            
            # Check stop loss
            if self.strategy.should_stop_loss(trade.price, current_price, self.stop_loss_percent):
                logger.info(f"Stop loss triggered for trade {trade.trade_id}")
                self.close_trade(trade, current_price, "stop_loss")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking take profit/stop loss: {e}")
            return False
    
    def close_trade(self, trade: Trade, close_price: float, reason: str) -> None:
        """
        Close a trade.
        
        Args:
            trade: Trade to close
            close_price: Price at which to close
            reason: Reason for closing
        """
        try:
            # Calculate profit/loss
            if trade.side == "buy":
                profit_loss = (close_price - trade.price) * trade.quantity
                profit_loss_percent = ((close_price - trade.price) / trade.price) * 100
            else:
                profit_loss = (trade.price - close_price) * trade.quantity
                profit_loss_percent = ((trade.price - close_price) / trade.price) * 100
            
            # Place sell order if it was a buy trade
            if trade.side == "buy":
                sell_trade = self.trader.place_sell_order(self.pair, trade.quantity)
                close_price = sell_trade.price  # Use actual executed price
            
            # Update trade
            trade.status = TradeStatus.CLOSED
            trade.close_price = close_price
            trade.close_timestamp = datetime.now()
            trade.profit_loss = profit_loss
            trade.profit_loss_percent = profit_loss_percent
            
            # Save to Firebase
            self.firebase.update_trade(trade)
            
            logger.info(f"Trade {trade.trade_id} closed. P/L: {profit_loss:.2f} NOK ({profit_loss_percent:.2f}%)")
            
        except Exception as e:
            logger.error(f"Error closing trade: {e}")
    
    def execute_buy_signal(self, signal) -> None:
        """
        Execute a buy signal.
        
        Args:
            signal: Buy signal
        """
        try:
            # Check if we already have an open trade
            if self.get_open_trade():
                logger.warning("Cannot execute buy signal: open trade already exists")
                return
            
            # Get available balance
            balance_nok = self.trader.get_balance("NOK")
            if balance_nok < 100:  # Minimum trade amount
                logger.warning(f"Insufficient balance: {balance_nok} NOK")
                return
            
            # Calculate quantity (use 95% of balance to leave some margin)
            quantity = (balance_nok * 0.95) / signal.price
            
            # Place buy order
            trade = self.trader.place_buy_order(self.pair, quantity)
            
            # Set take profit and stop loss
            trade.take_profit = trade.price * (1 + self.take_profit_percent / 100)
            trade.stop_loss = trade.price * (1 - self.stop_loss_percent / 100)
            
            # Save to Firebase
            self.firebase.save_trade(trade)
            
            logger.info(f"Buy order executed: {trade.quantity} {self.pair.split('/')[0]} at {trade.price} NOK")
            
        except Exception as e:
            logger.error(f"Error executing buy signal: {e}")
    
    def execute_sell_signal(self, signal, trade: Trade) -> None:
        """
        Execute a sell signal.
        
        Args:
            signal: Sell signal
            trade: Open trade to close
        """
        try:
            current_price = self.data_fetcher.get_latest_price(self.pair)
            self.close_trade(trade, current_price, "strategy_signal")
            
        except Exception as e:
            logger.error(f"Error executing sell signal: {e}")
    
    def update_portfolio_state(self) -> None:
        """Update and save portfolio state to Firebase."""
        try:
            balance_nok = self.trader.get_balance("NOK")
            balance_btc = self.trader.get_balance("BTC")
            
            # Get current BTC price
            current_price = self.data_fetcher.get_latest_price(self.pair)
            total_value_nok = balance_nok + (balance_btc * current_price)
            
            # Get trade statistics
            all_trades = self.firebase.get_all_trades(pair=self.pair)
            open_trades = [t for t in all_trades if t.status == TradeStatus.OPEN]
            closed_trades = [t for t in all_trades if t.status == TradeStatus.CLOSED]
            
            total_profit_loss = sum(t.profit_loss or 0.0 for t in closed_trades)
            total_profit_loss_percent = sum(t.profit_loss_percent or 0.0 for t in closed_trades) / len(closed_trades) if closed_trades else 0.0
            
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
            
            self.firebase.save_portfolio_state(portfolio)
            
        except Exception as e:
            logger.error(f"Error updating portfolio state: {e}")
    
    def run_iteration(self) -> None:
        """Run one iteration of the trading loop."""
        try:
            logger.info("Starting trading iteration")
            
            # Fetch latest candles
            candles = self.data_fetcher.get_candles(
                pair=self.pair,
                interval=self.candle_interval,
                limit=max(self.long_sma_period, self.long_sma_for_ema) + 10
            )
            
            if not candles:
                logger.warning("No candles fetched")
                return
            
            # Save latest price snapshot
            self.firebase.save_price_snapshot(candles[-1], self.pair)
            
            # Check for open trade
            open_trade = self.get_open_trade()
            
            # Check take profit/stop loss if we have an open trade
            if open_trade:
                if self.check_take_profit_stop_loss(open_trade):
                    # Trade was closed, refresh open_trade
                    open_trade = None
            
            # Generate signal
            signal = self.strategy.generate_signal(candles, has_open_trade=open_trade is not None)
            
            # Save signal to Firebase
            self.firebase.save_signal(signal)
            
            logger.info(f"Signal generated: {signal.signal_type.value} - {signal.reason}")
            
            # Execute signal
            if signal.signal_type == SignalType.BUY and not open_trade:
                self.execute_buy_signal(signal)
            elif signal.signal_type == SignalType.SELL and open_trade:
                self.execute_sell_signal(signal, open_trade)
            
            # Update portfolio state
            self.update_portfolio_state()
            
            logger.info("Trading iteration completed")
            
        except Exception as e:
            logger.error(f"Error in trading iteration: {e}", exc_info=True)
    
    def run(self) -> None:
        """Run the main trading loop."""
        logger.info("Starting trading bot")
        
        try:
            while True:
                self.run_iteration()
                logger.info(f"Sleeping for {self.poll_interval} seconds")
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logger.info("Trading bot stopped by user")
        except Exception as e:
            logger.error(f"Fatal error in trading bot: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    bot = TradingBot()
    bot.run()

