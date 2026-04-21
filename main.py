"""
Main trading bot orchestrator.
Runs continuous loop or single iteration (cron mode).
Fetches data, generates signals, executes trades when enabled, saves to Firestore.
"""
import argparse
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

from data_fetcher import FiriDataFetcher
from indicators import calculate_ema
from strategy import TradingStrategy
from trader import FiriTrader, round_price, round_quantity
from firebase_store import FirebaseStore, FirebaseLoggingHandler
from models import Trade, TradeStatus, Signal, SignalType, PortfolioState, Candle
from settings import (
    CANDLE_INTERVAL,
    CANDLE_LIMIT,
    STARTUP_CANDLE_LIMIT,
    BUY_QUOTE_AMOUNT,
    FIRI_FEE_PERCENT,
    SECONDS_PER_CANDLE,
    TRADING_ENABLED,
    TRADING_PAIR,
    SHORT_EMA_PERIOD,
    MEDIUM_EMA_PERIOD,
    LONG_EMA_PERIOD,
    POLL_INTERVAL,
)

load_dotenv()

# Configure logging (Firebase handler added in TradingBot.__init__)
_log_handlers = [logging.StreamHandler()]
try:
    _log_handlers.append(logging.FileHandler('trading_bot.log'))
except OSError:
    pass  # Skip file log on Render/cron (no writable dir)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=_log_handlers
)
logger = logging.getLogger(__name__)


class TradingBot:
    """Main trading bot orchestrator."""
    
    def __init__(self):
        """Initialize trading bot with all components."""
        self.pair = TRADING_PAIR
        self.poll_interval = POLL_INTERVAL
        self.trailing_stop_loss_percent = float(os.getenv("TRAILING_STOP_LOSS_PERCENT", "7.0"))
        self.cooldown_candles = int(os.getenv("COOLDOWN_CANDLES", "25"))
        
        # Initialize components
        self.data_fetcher = FiriDataFetcher()
        self.strategy = TradingStrategy(
            short_ema_period=SHORT_EMA_PERIOD,
            medium_ema_period=MEDIUM_EMA_PERIOD,
            long_ema_period=LONG_EMA_PERIOD,
        )
        self.trader = FiriTrader()
        self.firebase = FirebaseStore()

        # Fetch order format from Firi orderbook (price/amount decimals)
        firi_format = self.data_fetcher.get_order_format(self.pair)
        if firi_format:
            self.trader.price_decimals, self.trader.quantity_decimals = firi_format
            logger.info(f"Using Firi order format: price_decimals={self.trader.price_decimals}, "
                       f"quantity_decimals={self.trader.quantity_decimals}")
        else:
            raise ValueError(
                f"Could not fetch order format from Firi for pair {self.pair}. "
                f"Pair may not exist on Firi (e.g. invalid TRADING_PAIR in trading_config.py)."
            )

        # Add Firebase logging handler (WARNING by default to stay within Firestore limits)
        firebase_handler = FirebaseLoggingHandler(self.firebase)
        fb_level = os.getenv("FIREBASE_LOG_LEVEL", "WARNING").upper()
        firebase_handler.setLevel(getattr(logging, fb_level, logging.ERROR))
        firebase_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(firebase_handler)

        logger.info(f"Trading bot initialized for pair: {self.pair}")
        logger.info(f"Mode: {'TRADING' if TRADING_ENABLED else 'MONITOR (prices only, no orders)'}")
        logger.info(f"EMA periods: Short={self.strategy.short_ema_period}, "
                   f"Medium={self.strategy.medium_ema_period}, "
                   f"Long={self.strategy.long_ema_period}")
        logger.info(f"Poll interval: {self.poll_interval} seconds")
        logger.info(f"Trailing stop loss: {self.trailing_stop_loss_percent}%")
        logger.info(f"Cooldown: {self.cooldown_candles} candles")
        quote_ccy = self.pair.split("/")[1]
        logger.info(
            f"Fixed buy size: {BUY_QUOTE_AMOUNT} {quote_ccy} per order "
            f"(quantity from ~{FIRI_FEE_PERCENT}% fee-adjusted notional)"
        )
    
    def initialize(self) -> None:
        """Initialize and load initial data at startup from Firebase only."""
        logger.info(
            f"Loading initial candle data from Firebase "
            f"({STARTUP_CANDLE_LIMIT} candles, {CANDLE_INTERVAL} interval)..."
        )

        try:
            candles = self.firebase.get_price_snapshots(
                pair=self.pair,
                limit=STARTUP_CANDLE_LIMIT
            )
            if candles:
                logger.info(f"Loaded {len(candles)} candles from Firebase")

                # Backfill latest 50 EMA values (short, medium, long) going back from latest
                self.firebase.clear_ema_for_pair(self.pair)
                self._backfill_ema_history(candles, limit=50)
            else:
                logger.warning(
                    "No candles found in Firebase at startup. "
                    "First cron runs must populate prices before EMA backfill is available."
                )
        except Exception as e:
            logger.error(f"Error loading initial candles from Firebase: {e}", exc_info=True)
            raise

    def _backfill_ema_history(self, candles: list[Candle], limit: int = 50) -> None:
        """
        Calculate and save the latest N EMA values (short, medium, long) going back from latest price.
        """
        if len(candles) < self.strategy.long_ema_period:
            logger.warning(
                f"Insufficient candles for EMA backfill: {len(candles)} < {self.strategy.long_ema_period}"
            )
            return
        short_ema = calculate_ema(candles, self.strategy.short_ema_period)
        medium_ema = calculate_ema(candles, self.strategy.medium_ema_period)
        long_ema = calculate_ema(candles, self.strategy.long_ema_period)
        count = 0
        for i in range(len(candles) - 1, -1, -1):
            if count >= limit:
                break
            if short_ema[i] is not None and medium_ema[i] is not None and long_ema[i] is not None:
                self.firebase.save_ema_values(
                    pair=self.pair,
                    timestamp=candles[i].timestamp,
                    short_ema=short_ema[i],
                    medium_ema=medium_ema[i],
                    long_ema=long_ema[i],
                )
                count += 1
        logger.info(f"Backfilled {count} EMA values (short, medium, long) to Firebase")

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
            interval=CANDLE_INTERVAL,
            limit=self.cooldown_candles + 10
        )
        
        if not candles or len(candles) < self.cooldown_candles:
            return False
        
        # Check if last sell was within cooldown period
        if last_trade.close_timestamp:
            time_since_sell = datetime.now() - last_trade.close_timestamp
            candles_since_sell = int(time_since_sell.total_seconds() / SECONDS_PER_CANDLE)
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

            if BUY_QUOTE_AMOUNT <= 0:
                logger.error("BUY_QUOTE_AMOUNT must be positive; skipping buy")
                return

            spend_total = BUY_QUOTE_AMOUNT
            if balance < spend_total:
                logger.warning(
                    f"Insufficient balance for fixed buy: {balance:.2f} {quote_currency} "
                    f"(need {spend_total:.2f})"
                )
                return

            # Match scripts/test_trade.py: fee reduces quote notional before converting to base quantity
            amount_for_purchase = spend_total / (1 + FIRI_FEE_PERCENT / 100.0)
            order_price = round_price(current_price, self.trader.price_decimals)
            quantity = round_quantity(
                amount_for_purchase / current_price,
                self.trader.quantity_decimals,
            )
            if quantity <= 0:
                logger.warning("Computed buy quantity <= 0; skipping")
                return

            # Place buy order
            trade = self.trader.place_buy_order(
                pair=self.pair,
                quantity=quantity,
                price=order_price,
            )
            
            # Initialize highest price for trailing stop
            trade.highest_price = current_price
            
            # Save to Firebase
            self.firebase.save_trade(trade)
            
            pd, qd = self.trader.price_decimals, self.trader.quantity_decimals
            logger.info(
                f"Buy order placed: {quantity:.{qd}f} {self.pair.split('/')[0]} at {order_price:.{pd}f} "
                f"{quote_currency} (~{spend_total:.2f} {quote_currency} incl. fee)"
            )
            
        except Exception as e:
            logger.error(f"Error executing buy signal: {e}", exc_info=True)
    
    def update_portfolio_state(self) -> None:
        """Update and save portfolio state to Firebase."""
        try:
            # Get balances
            base_currency = self.pair.split('/')[0]  # e.g., "ETH"
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
            # Fetch candles
            candles = self.data_fetcher.get_candles(
                pair=self.pair,
                interval=CANDLE_INTERVAL,
                limit=CANDLE_LIMIT
            )
            
            if not candles or len(candles) < self.strategy.long_ema_period:
                logger.warning(f"Insufficient candles: {len(candles) if candles else 0} < {self.strategy.long_ema_period}")
                return

            # Remove any prices from other pairs (e.g. stray DKK if another bot instance ran)
            self.firebase.clear_prices_for_other_pairs(keep_pair=self.pair)
            
            # Save price snapshot
            self.save_price_snapshot(candles)
            
            # Get current price
            current_price = candles[-1].close
            
            # Get open trade
            open_trade = self.get_open_trade()
            
            # Check trailing stop loss if we have an open trade (only when trading)
            if open_trade and TRADING_ENABLED:
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

            # Save EMA values to ema_short, ema_medium, ema_long collections
            self.firebase.save_ema_values(
                pair=self.pair,
                timestamp=signal.timestamp,
                short_ema=signal.short_ema,
                medium_ema=signal.medium_ema,
                long_ema=signal.long_ema,
            )
            
            logger.info(f"Signal generated: {signal.signal_type.value.upper()} - {signal.reason}")
            if signal.short_ema:
                logger.info(f"  Short EMA: {signal.short_ema:.2f}")
            if signal.medium_ema:
                logger.info(f"  Medium EMA: {signal.medium_ema:.2f}")
            if signal.long_ema:
                logger.info(f"  Long EMA: {signal.long_ema:.2f}")
            
            # Execute signal (only when trading enabled; otherwise just log)
            if TRADING_ENABLED:
                if signal.signal_type == SignalType.BUY and not open_trade:
                    self.execute_buy_signal(signal, current_price)
                elif signal.signal_type == SignalType.SELL and open_trade:
                    self.close_trade(open_trade, signal.reason)
                self.update_portfolio_state()
            else:
                if signal.signal_type == SignalType.BUY:
                    logger.info("(Monitor mode - BUY signal not executed)")
                elif signal.signal_type == SignalType.SELL and open_trade:
                    logger.info("(Monitor mode - SELL signal not executed)")
            
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
    parser = argparse.ArgumentParser(description="Trading bot: fetch data, signals, orders → Firestore")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one iteration and exit (for cron jobs)",
    )
    args = parser.parse_args()

    bot = TradingBot()
    bot.initialize()  # Load initial data (200 candles), clear prices, save to Firebase

    if args.once:
        logger.info("Cron mode: running single iteration")
        bot.run_iteration()
        logger.info("Cron run complete")
    else:
        bot.run()


if __name__ == "__main__":
    main()
