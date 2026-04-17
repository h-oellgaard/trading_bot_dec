#!/usr/bin/env python3
"""
Check Firi saldo og historikk. Bruker firipy (simple auth).
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from firipy import FiriAPI

def main():
    api_key = os.getenv("FIRI_API_KEY")
    if not api_key:
        print("FIRI_API_KEY mangler i .env")
        sys.exit(1)

    api = FiriAPI(api_key)

    print("=== SALDO ===")
    try:
        balances = api.balances()
        for b in balances:
            if isinstance(b, dict):
                cur = b.get("currency", "")
                avail = float(b.get("available", 0))
                bal = float(b.get("balance", 0))
                hold = float(b.get("hold", 0))
                if avail > 0 or bal > 0 or hold > 0:
                    print(f"  {cur}: {avail:.8f} tilgjengelig, {bal:.8f} total, {hold:.8f} hold")
        else:
            print(balances)
    except Exception as e:
        print(f"Feil ved saldo: {e}")

    print("\n=== ÅPNE ORDRE ===")
    try:
        orders = api.orders()
        if isinstance(orders, list) and orders:
            for o in orders[:20]:
                print(f"  {o}")
        elif isinstance(orders, dict):
            print(f"  {orders}")
        else:
            print("  Ingen åpne ordre")
    except Exception as e:
        print(f"Feil ved åpne ordre: {e}")

    print("\n=== ORDREHISTORIKK (ETHDKK, siste 20) ===")
    try:
        hist = api.orders_market_history("ETHDKK", count=20)
        if isinstance(hist, list) and hist:
            for o in hist:
                if isinstance(o, dict):
                    oid = o.get("id", o.get("order_id", "?"))
                    t = o.get("type", o.get("side", "?"))
                    amt = o.get("amount", o.get("amount_currency", "?"))
                    pr = o.get("price", "?")
                    mat = o.get("matched", "0")
                    created = o.get("created_at", o.get("date", ""))
                    print(f"  {oid}: {t} {amt} @ {pr} (matched: {mat}) {created}")
                else:
                    print(f"  {o}")
        elif isinstance(hist, dict):
            print(f"  {hist}")
        else:
            print("  Ingen historikk")
    except Exception as e:
        print(f"Feil ved ordrehistorikk: {e}")

    print("\n=== TRANSAKSJONER (siste 10) ===")
    try:
        tx = api.history_transactions(count=10)
        if isinstance(tx, list) and tx:
            for t in tx[:10]:
                if isinstance(t, dict):
                    tid = t.get("id", "?")
                    amt = t.get("amount", "?")
                    cur = t.get("currency", "?")
                    typ = t.get("type", "?")
                    dt = t.get("date", t.get("date", ""))
                    print(f"  {tid}: {typ} {amt} {cur} {dt}")
                else:
                    print(f"  {t}")
        elif isinstance(tx, dict):
            print(f"  {tx}")
        else:
            print("  Ingen transaksjoner")
    except Exception as e:
        print(f"Feil ved transaksjoner: {e}")

    # Sjekk spesifikk ordre hvis ID er gitt
    if len(sys.argv) > 1:
        oid = sys.argv[1]
        print(f"\n=== ORDRE {oid} ===")
        try:
            o = api.order(oid)
            print(o)
        except Exception as e:
            print(f"Feil: {e}")


if __name__ == "__main__":
    main()
