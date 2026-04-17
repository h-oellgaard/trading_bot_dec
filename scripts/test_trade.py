#!/usr/bin/env python3
"""
Execute a test buy order using the bot's trading code.
Usage: python scripts/test_trade.py [amount]
  amount: Spend this much in quote currency (default 200), including 0.7% Firi fee.

Uses TRADING_PAIR from trading_config.
For 200 DKK test: set TRADING_PAIR = "ETH/DKK" in trading_config.py.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from settings.trading_config import TRADING_PAIR
from data_fetcher import FiriDataFetcher
from trader import FiriTrader

FIRI_FEE_PERCENT = 0.7  # Firi charges 0.7% per trade


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    flags = [a for a in sys.argv[1:] if a.startswith("-")]
    amount_quote = float(args[0]) if args else 200.0
    skip_confirm = "--yes" in flags or "-y" in flags
    if amount_quote <= 0:
        print("Amount must be positive")
        sys.exit(1)

    base_currency = TRADING_PAIR.split("/")[0]
    quote_currency = TRADING_PAIR.split("/")[1]
    print(f"Test trade: {amount_quote} {quote_currency} (including {FIRI_FEE_PERCENT}% fee)")
    print(f"Pair: {TRADING_PAIR}")

    fetcher = FiriDataFetcher()
    trader = FiriTrader()

    # Get order format
    firi_format = fetcher.get_order_format(TRADING_PAIR)
    if firi_format:
        trader.price_decimals, trader.quantity_decimals = firi_format

    # Get current price (use ask for buy - we pay the ask)
    price = fetcher.get_ticker_price(TRADING_PAIR)
    if not price or price <= 0:
        print("Could not get current price")
        sys.exit(1)
    print(f"Current price: {price:.2f} {quote_currency}")

    # Amount after fee: we spend amount_quote total, fee is 0.7%
    # cost_before_fee * (1 + 0.007) = amount_quote
    # cost_before_fee = amount_quote / 1.007
    amount_for_purchase = amount_quote / (1 + FIRI_FEE_PERCENT / 100)
    quantity = amount_for_purchase / price
    fee_amount = amount_quote - amount_for_purchase

    print(f"Quantity: {quantity:.8f} {base_currency}")
    print(f"Fee (~{FIRI_FEE_PERCENT}%): {fee_amount:.2f} {quote_currency}")
    print(f"Total: {amount_quote:.2f} {quote_currency}")

    # Check balance
    balance = trader.get_balance(currency=quote_currency)
    if balance < amount_quote:
        print(f"Insufficient balance: {balance:.2f} {quote_currency} (need {amount_quote:.2f})")
        sys.exit(1)
    print(f"Balance: {balance:.2f} {quote_currency}")

    if not skip_confirm:
        confirm = input("\nPlace order? [y/N]: ")
        if confirm.lower() != "y":
            print("Aborted")
            sys.exit(0)

    trade = trader.place_buy_order(
        pair=TRADING_PAIR,
        quantity=quantity,
        price=price,
    )
    print(f"\nOrder placed: {trade.trade_id}")
    print(f"  {trade.quantity:.8f} {base_currency} @ {trade.price:.2f} {quote_currency}")


if __name__ == "__main__":
    main()
