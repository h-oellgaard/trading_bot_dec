import logging
import time
from datetime import datetime
from typing import Optional, List

from .strategies.sma_cross import SmaCrossStrategy
from .domain.strategy import TradingStrategy
from .domain.coin import Coin
from .domain.trade import Trade
from .data_manager import DataManager

logger = logging.getLogger(__name__)


class TradingEngine:
    """Main trading engine that coordinates strategy execution and data management"""
    
    def __init__(self, strategy: TradingStrategy, symbols: List[str], 
                 interval: int = 60, project_id: Optional[str] = None):
        """
        Initialize the trading engine
        
        Args:
            strategy: Trading strategy to use
            symbols: List of cryptocurrency symbols to trade
            interval: Trading interval in seconds
            project_id: Google Cloud project ID for Firestore (optional)
        """
        self.strategy = strategy
        self.symbols = symbols
        self.interval = interval
        self.data_manager = DataManager(project_id=project_id)
        self.running = False
        
        logger.info(f"Trading engine initialized with {len(symbols)} symbols, interval: {interval}s")
    
    def start(self):
        """Start the trading engine"""
        if self.running:
            logger.warning("Trading engine is already running")
            return
        
        self.running = True
        logger.info("Starting trading engine...")
        
        # Start background data collection
        self.data_manager.start_data_collection(self.symbols, interval=self.interval)
        
        try:
            while self.running:
                self._trading_cycle()
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping trading engine...")
        except Exception as e:
            logger.error(f"Error in trading engine: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the trading engine"""
        self.running = False
        self.data_manager.stop_data_collection()
        logger.info("Trading engine stopped")
    
    def _trading_cycle(self):
        """Execute one trading cycle for all symbols"""
        logger.debug("Starting trading cycle")
        
        for symbol in self.symbols:
            try:
                self._process_symbol(symbol)
            except Exception as e:
                logger.error(f"Error processing symbol {symbol}: {e}")
    
    def _process_symbol(self, symbol: str):
        """Process a single symbol for trading signals"""
        logger.debug(f"Processing symbol: {symbol}")
        
        # Get market data for strategy analysis
        # Use a reasonable number of periods based on strategy requirements
        required_periods = max(
            getattr(self.strategy, 'short_window', 20),
            getattr(self.strategy, 'long_window', 50)
        )
        
        market_data = self.data_manager.get_market_data(symbol, required_periods)
        
        if not market_data or len(market_data) < required_periods:
            logger.warning(f"Insufficient data for {symbol}: {len(market_data) if market_data else 0} periods")
            return
        
        # Generate trading signal
        signal = self.strategy.generate_signal(market_data)
        
        if signal:
            logger.info(f"Signal generated for {symbol}: {signal}")
            self._execute_signal(symbol, signal, market_data.get_latest_price())
        else:
            logger.debug(f"No signal for {symbol}")
    
    def _execute_signal(self, symbol: str, signal: str, current_price: float):
        """Execute a trading signal"""
        try:
            # Create coin object
            coin = Coin(symbol=symbol, name=symbol.capitalize(), precision=8)
            
            # Create trade object
            trade = Trade(
                coin=coin,
                action=signal,
                amount=0.1,  # Fixed amount for demo - should be calculated based on position sizing
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.strategy.__class__.__name__
            )
            
            # Save trade to Firestore
            success = self.data_manager.save_trade(trade)
            
            if success:
                logger.info(f"Trade executed: {trade.id} - {symbol} {signal} {trade.amount} @ ${current_price:,.2f}")
            else:
                logger.error(f"Failed to save trade for {symbol}")
                
        except Exception as e:
            logger.error(f"Error executing signal for {symbol}: {e}")
    
    def get_trading_statistics(self, symbol: Optional[str] = None) -> dict:
        """Get trading statistics"""
        return self.data_manager.get_trading_statistics(symbol=symbol)
    
    def get_data_statistics(self, symbol: str) -> dict:
        """Get data statistics for a symbol"""
        return self.data_manager.get_data_statistics(symbol)
    
    def get_recent_trades(self, symbol: Optional[str] = None, limit: int = 10) -> List[Trade]:
        """Get recent trades"""
        return self.data_manager.get_trades(symbol=symbol, limit=limit)


def main():
    """Main function to run the trading engine"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize strategy
    strategy = SmaCrossStrategy(short_window=5, long_window=20)
    
    # Define symbols to trade
    symbols = ['bitcoin', 'ethereum']
    
    # Create and start trading engine
    engine = TradingEngine(
        strategy=strategy,
        symbols=symbols,
        interval=60,  # 1 minute intervals
        project_id=None  # Use default project
    )
    
    try:
        engine.start()
    except KeyboardInterrupt:
        print("\nStopping trading engine...")


if __name__ == "__main__":
    main() 