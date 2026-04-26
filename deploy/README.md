# VPS deployment files

Use these after cloning the repo on your server (paths assume `/home/tradingbot/trading-bot`; change `User`/`WorkingDirectory` in the unit file if needed).

| File | Purpose |
|------|---------|
| `trading-bot.service` | systemd: continuous `main.py` loop |
| `logrotate-trading-bot` | rotate `trading_bot.log` |
| `install-vps.sh` | `python3 -m venv venv` + `pip install -r requirements-prod.txt` |
| `trading-bot.cron.example` | example crontab line for `main.py --once` |
| `../requirements-prod.txt` | runtime deps only (no pytest) |

## Quick sequence

1. `git clone … && cd trading-bot`
2. `./deploy/install-vps.sh` (or create `venv` manually and `pip install -r requirements-prod.txt`)
3. `cp .env.example .env` → fill `FIRI_*`, `FIRI_CLIENT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, set `TRADING_ENABLED` when ready
4. `chmod 600 .env` and restrict the Firebase JSON key (`chmod 600 service-account-key.json`)
5. Edit paths/user in `deploy/trading-bot.service`, then:
   - `sudo cp deploy/trading-bot.service /etc/systemd/system/trading-bot.service`
   - `sudo systemctl daemon-reload && sudo systemctl enable --now trading-bot`
6. Optional: `sudo cp deploy/logrotate-trading-bot /etc/logrotate.d/trading-bot`
7. Logs: `sudo journalctl -u trading-bot -f` and/or `tail -f trading_bot.log`

## Cron instead of systemd

Use the same venv: `/home/tradingbot/trading-bot/venv/bin/python /home/tradingbot/trading-bot/main.py --once` on your schedule (see `render.yaml` for an example).

Full narrative (Danish): `documentation/DEPLOYMENT.md`.
