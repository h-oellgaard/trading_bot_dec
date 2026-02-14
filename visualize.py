"""
Visualization module for trading bot data using matplotlib.
Shows candles, indicators, signals, and trades.
"""
import os
import matplotlib
# Set backend explicitly for Windows
matplotlib.use('TkAgg')  # Use TkAgg backend which works well on Windows
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Optional, List
from dotenv import load_dotenv

from firebase_store import FirebaseStore
from data_fetcher import FiriDataFetcher
from indicators import calculate_ema
from models import Candle, Trade, Signal
from settings.trading_config import (
    TRADING_PAIR,
    SHORT_EMA_PERIOD,
    MEDIUM_EMA_PERIOD,
    LONG_EMA_PERIOD,
)

load_dotenv()


class TradingVisualizer:
    """Visualizes trading data using matplotlib."""

    def __init__(self):
        self.firebase = FirebaseStore()
        self.data_fetcher = FiriDataFetcher()
        self.pair = TRADING_PAIR
        self.short_ema_period = SHORT_EMA_PERIOD
        self.medium_ema_period = MEDIUM_EMA_PERIOD
        self.long_ema_period = LONG_EMA_PERIOD
    
    def plot_trading_chart(
        self,
        candles: List[Candle],
        trades: Optional[List[Trade]] = None,
        signals: Optional[List[Signal]] = None,
        show_indicators: bool = True,
        days_back: int = 7
    ):
        """
        Plot a comprehensive trading chart with candles, indicators, trades, and signals.
        
        Args:
            candles: List of Candle objects
            trades: Optional list of Trade objects
            signals: Optional list of Signal objects
            show_indicators: Whether to show SMA/EMA indicators
            days_back: Number of days to show (filters candles)
        """
        if not candles:
            print("No candles to plot")
            return
        
        # Filter candles by date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        # Make cutoff_date timezone-aware if candles are timezone-aware
        if candles and candles[0].timestamp.tzinfo is not None:
            from datetime import timezone
            if cutoff_date.tzinfo is None:
                cutoff_date = cutoff_date.replace(tzinfo=timezone.utc)
        filtered_candles = [c for c in candles if c.timestamp >= cutoff_date]
        
        if not filtered_candles:
            print(f"No candles found in the last {days_back} days")
            return
        
        # Prepare data
        timestamps = [c.timestamp for c in filtered_candles]
        opens = [c.open for c in filtered_candles]
        highs = [c.high for c in filtered_candles]
        lows = [c.low for c in filtered_candles]
        closes = [c.close for c in filtered_candles]
        volumes = [c.volume for c in filtered_candles]
        
        # Create figure with subplots
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(4, 1, height_ratios=[3, 1, 1, 1], hspace=0.3)
        
        # Main price chart
        ax1 = fig.add_subplot(gs[0])
        
        # Plot candles
        for i, candle in enumerate(filtered_candles):
            color = 'green' if candle.close >= candle.open else 'red'
            ax1.plot([timestamps[i], timestamps[i]], [candle.low, candle.high], 
                    color='black', linewidth=0.5, alpha=0.5)
            ax1.bar(timestamps[i], abs(candle.close - candle.open), 
                   bottom=min(candle.open, candle.close),
                   color=color, alpha=0.7, width=0.0005)
        
        # Calculate and plot indicators
        if show_indicators:
            ema_short = calculate_ema(filtered_candles, self.short_ema_period)
            ema_medium = calculate_ema(filtered_candles, self.medium_ema_period)
            ema_long = calculate_ema(filtered_candles, self.long_ema_period)
            
            if ema_short:
                ax1.plot(timestamps[-len(ema_short):], ema_short, 
                        label=f'Short EMA({self.short_ema_period})', 
                        color='blue', linewidth=1.5, alpha=0.7)
            if ema_medium:
                ax1.plot(timestamps[-len(ema_medium):], ema_medium, 
                        label=f'Medium EMA({self.medium_ema_period})', 
                        color='green', linewidth=1.5, alpha=0.7)
            if ema_long:
                ax1.plot(timestamps[-len(ema_long):], ema_long, 
                        label=f'Long EMA({self.long_ema_period})', 
                        color='orange', linewidth=1.5, alpha=0.7)
        
        # Plot trades
        if trades:
            buy_trades = [t for t in trades if t.side == "buy" and t.timestamp >= cutoff_date]
            sell_trades = [t for t in trades if t.side == "sell" and t.timestamp >= cutoff_date]
            
            for trade in buy_trades:
                ax1.scatter(trade.timestamp, trade.price, color='green', 
                           marker='^', s=200, zorder=5, label='Buy' if trade == buy_trades[0] else '')
                ax1.annotate(f'Buy\n{trade.price:.0f}', 
                           (trade.timestamp, trade.price),
                           xytext=(10, 10), textcoords='offset points',
                           fontsize=8, bbox=dict(boxstyle='round,pad=0.3', 
                           facecolor='green', alpha=0.3))
            
            for trade in sell_trades:
                ax1.scatter(trade.timestamp, trade.price, color='red', 
                           marker='v', s=200, zorder=5, label='Sell' if trade == sell_trades[0] else '')
                ax1.annotate(f'Sell\n{trade.price:.0f}', 
                           (trade.timestamp, trade.price),
                           xytext=(10, -20), textcoords='offset points',
                           fontsize=8, bbox=dict(boxstyle='round,pad=0.3', 
                           facecolor='red', alpha=0.3))
        
        # Plot signals
        if signals:
            buy_signals = [s for s in signals if s.signal_type.value == "buy" and s.timestamp >= cutoff_date]
            sell_signals = [s for s in signals if s.signal_type.value == "sell" and s.timestamp >= cutoff_date]
            
            for signal in buy_signals:
                ax1.scatter(signal.timestamp, signal.price, color='lime', 
                           marker='*', s=300, zorder=4, alpha=0.6,
                           label='Buy Signal' if signal == buy_signals[0] else '')
            
            for signal in sell_signals:
                ax1.scatter(signal.timestamp, signal.price, color='orange', 
                           marker='*', s=300, zorder=4, alpha=0.6,
                           label='Sell Signal' if signal == sell_signals[0] else '')
        
        ax1.set_title(f'{self.pair} Trading Chart - Last {days_back} Days', fontsize=14, fontweight='bold')
        quote_currency = self.pair.split('/')[1] if '/' in self.pair else 'NOK'
        ax1.set_ylabel(f'Price ({quote_currency})', fontsize=12)
        ax1.legend(loc='upper left', fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax1.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Volume chart
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        colors = ['green' if closes[i] >= opens[i] else 'red' for i in range(len(filtered_candles))]
        ax2.bar(timestamps, volumes, color=colors, alpha=0.5, width=0.0005)
        ax2.set_ylabel('Volume', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_title('Volume', fontsize=10)
        
        # P/L chart (if trades available)
        if trades:
            ax3 = fig.add_subplot(gs[2], sharex=ax1)
            closed_trades = [t for t in trades if t.status.value == "closed" and t.timestamp >= cutoff_date]
            if closed_trades:
                cumulative_pnl = []
                cumulative_value = 0
                trade_times = []
                for trade in sorted(closed_trades, key=lambda t: t.close_timestamp or t.timestamp):
                    if trade.profit_loss is not None:
                        cumulative_value += trade.profit_loss
                        cumulative_pnl.append(cumulative_value)
                        trade_times.append(trade.close_timestamp or trade.timestamp)
                
                if cumulative_pnl:
                    ax3.plot(trade_times, cumulative_pnl, color='blue', linewidth=2, marker='o')
                    ax3.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
                    ax3.fill_between(trade_times, 0, cumulative_pnl, 
                                    where=[p >= 0 for p in cumulative_pnl], 
                                    color='green', alpha=0.3, label='Profit')
                    ax3.fill_between(trade_times, 0, cumulative_pnl, 
                                    where=[p < 0 for p in cumulative_pnl], 
                                    color='red', alpha=0.3, label='Loss')
                    quote_currency = self.pair.split('/')[1] if '/' in self.pair else 'NOK'
                    ax3.set_ylabel(f'Cumulative P/L ({quote_currency})', fontsize=10)
                    ax3.set_title('Cumulative Profit/Loss', fontsize=10)
                    ax3.legend(loc='upper left', fontsize=8)
                    ax3.grid(True, alpha=0.3)
        
        # Portfolio value chart
        ax4 = fig.add_subplot(gs[3], sharex=ax1)
        # This would require portfolio state data - simplified for now
        ax4.text(0.5, 0.5, 'Portfolio Value Chart\n(Requires portfolio state data)', 
                ha='center', va='center', transform=ax4.transAxes, fontsize=12)
        quote_currency = self.pair.split('/')[1] if '/' in self.pair else 'NOK'
        ax4.set_ylabel(f'Value ({quote_currency})', fontsize=10)
        ax4.set_xlabel('Time', fontsize=10)
        
        plt.tight_layout()
        return fig
    
    def visualize_from_firebase(self, days_back: int = 7):
        """Fetch data from Firebase and visualize."""
        print(f"Fetching data from Firebase for {self.pair}...")
        
        # Fetch candles from API (more reliable than Firebase for recent data)
        print("Fetching candles from API...")
        candles = self.data_fetcher.get_candles(
            pair=self.pair,
            interval="1h",
            limit=days_back * 24  # Approximate candles needed
        )
        
        if not candles:
            print("No candles found")
            return
        
        # Fetch trades from Firebase
        print("Fetching trades from Firebase...")
        trades = self.firebase.get_all_trades(pair=self.pair)
        
        # Fetch recent signals from Firebase
        print("Fetching signals from Firebase...")
        signals = self.firebase.get_recent_signals(limit=100)
        # Note: Signals don't have pair attribute, so we keep all signals
        
        print(f"Found {len(candles)} candles, {len(trades)} trades, {len(signals)} signals")
        
        if not candles:
            print("No candles to visualize!")
            return
        
        # Plot
        fig = self.plot_trading_chart(candles, trades, signals, days_back=days_back)
        
        if fig is None:
            print("Failed to create chart!")
            return
        
        # Save figure as backup
        output_file = f"trading_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Chart saved to: {output_file}")
        
        # Ensure figure is shown
        try:
            plt.show(block=True)
            print("Chart displayed. Close the window to continue.")
        except Exception as e:
            print(f"Could not display chart interactively: {e}")
            print(f"Chart saved to file instead: {output_file}")
    
    def visualize_live(self, hours_back: int = 24):
        """Visualize live data from API."""
        print(f"Fetching live data for {self.pair}...")
        
        # Fetch candles
        candles = self.data_fetcher.get_candles(
            pair=self.pair,
            interval="1h",
            limit=hours_back
        )
        
        if not candles:
            print("No candles found")
            return
        
        # Fetch trades
        trades = self.firebase.get_all_trades(pair=self.pair)
        
        # Fetch signals
        signals = self.firebase.get_recent_signals(limit=50)
        
        # Convert hours_back to days for filtering
        days_back = max(1, hours_back / 24)
        
        if not candles:
            print("No candles to visualize!")
            return
        
        fig = self.plot_trading_chart(candles, trades, signals, days_back=days_back)
        
        if fig is None:
            print("Failed to create chart!")
            return
        
        # Save figure as backup
        output_file = f"trading_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Chart saved to: {output_file}")
        
        # Ensure figure is shown
        try:
            plt.show(block=True)
            print("Chart displayed. Close the window to continue.")
        except Exception as e:
            print(f"Could not display chart interactively: {e}")
            print(f"Chart saved to file instead: {output_file}")


if __name__ == "__main__":
    import sys
    
    visualizer = TradingVisualizer()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "live":
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            visualizer.visualize_live(hours_back=hours)
        elif sys.argv[1] == "firebase":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            visualizer.visualize_from_firebase(days_back=days)
        else:
            days = int(sys.argv[1]) if sys.argv[1].isdigit() else 7
            visualizer.visualize_from_firebase(days_back=days)
    else:
        # Default: visualize from Firebase, last 7 days
        visualizer.visualize_from_firebase(days_back=7)

