# 🔥 Firestore Integration Setup

This document explains how to set up and use Google Cloud Firestore for data persistence in the crypto trading bot.

## Overview

The trading bot uses Firestore to store:
- **Price Data**: Historical and real-time cryptocurrency prices
- **Trade Data**: All executed trades with metadata
- **Market Data**: Aggregated data for strategy analysis

## Prerequisites

1. **Google Cloud Account**: You need a Google Cloud account
2. **Firestore Database**: A Firestore database in your Google Cloud project
3. **Authentication**: Service account credentials

## Setup Instructions

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your **Project ID** (you'll need this later)

### 2. Enable Firestore

1. In the Google Cloud Console, go to **Firestore Database**
2. Click **Create Database**
3. Choose **Native mode** (recommended for new projects)
4. Select a location for your database
5. Click **Done**

### 3. Create Service Account

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Give it a name (e.g., `trading-bot-service`)
4. Add the **Cloud Datastore User** role
5. Click **Create and Continue**
6. Click **Done**

### 4. Download Credentials

1. Click on your service account
2. Go to the **Keys** tab
3. Click **Add Key** > **Create New Key**
4. Choose **JSON** format
5. Download the JSON file
6. **Important**: Keep this file secure and never commit it to version control

### 5. Set Environment Variable

Set the path to your credentials file as an environment variable:

```bash
# Linux/Mac
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

# Windows (PowerShell)
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\service-account-key.json"

# Windows (Command Prompt)
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account-key.json
```

## Installation

Install the required dependencies:

```bash
pip install google-cloud-firestore
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from src.data_manager import DataManager

# Initialize with your project ID
data_manager = DataManager(project_id='your-project-id')

# Start collecting data
symbols = ['bitcoin', 'ethereum', 'cardano']
data_manager.start_data_collection(symbols, interval=60)

# Get market data for strategy analysis
market_data = data_manager.get_market_data('bitcoin', periods=30)

# Save a trade
from src.domain.trade import Trade
from src.domain.coin import Coin

coin = Coin(symbol='bitcoin', name='Bitcoin', precision=8)
trade = Trade(
    coin=coin,
    action='BUY',
    amount=0.1,
    price=50000.0,
    timestamp=datetime.now(),
    strategy='SMA_CROSS'
)

data_manager.save_trade(trade)
```

### Trading Engine Integration

```python
from src.engine import TradingEngine
from src.strategies.sma_cross import SmaCrossStrategy

# Initialize strategy
strategy = SmaCrossStrategy(short_window=5, long_window=20)

# Create trading engine with Firestore
engine = TradingEngine(
    strategy=strategy,
    symbols=['bitcoin', 'ethereum'],
    interval=60,
    project_id='your-project-id'  # Optional if using environment variable
)

# Start trading
engine.start()
```

### Data Retrieval

```python
# Get recent trades
trades = data_manager.get_trades(symbol='bitcoin', limit=10)

# Get trading statistics
stats = data_manager.get_trading_statistics(symbol='bitcoin')

# Get data statistics
data_stats = data_manager.get_data_statistics('bitcoin')

# Get available symbols
symbols = data_manager.get_available_symbols()
```

## Data Structure

### Price Data Collection

```json
{
  "symbol": "bitcoin",
  "price": 50000.0,
  "volume": 1000000.0,
  "timestamp": "2024-01-15T10:30:00Z",
  "source": "coingecko",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Trade Data Collection

```json
{
  "id": "trade_123456",
  "symbol": "bitcoin",
  "action": "BUY",
  "amount": 0.1,
  "price": 50000.0,
  "timestamp": "2024-01-15T10:30:00Z",
  "strategy": "SMA_CROSS",
  "status": "PENDING",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Security Best Practices

1. **Never commit credentials**: Keep your service account key secure
2. **Use environment variables**: Set `GOOGLE_APPLICATION_CREDENTIALS` in your environment
3. **Limit permissions**: Only grant necessary roles to your service account
4. **Monitor usage**: Set up billing alerts in Google Cloud Console
5. **Regular backups**: Consider setting up automated backups

## Cost Considerations

Firestore pricing is based on:
- **Document reads**: $0.06 per 100,000 reads
- **Document writes**: $0.18 per 100,000 writes
- **Document deletes**: $0.02 per 100,000 deletes
- **Storage**: $0.18 per GB per month

For a typical trading bot:
- **Reads**: ~1,000-10,000 per day (depending on frequency)
- **Writes**: ~100-1,000 per day (price updates + trades)
- **Storage**: Minimal (a few MB per month)

Estimated cost: **$1-5 per month** for typical usage.

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```
   google.auth.exceptions.DefaultCredentialsError
   ```
   **Solution**: Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

2. **Permission Denied**
   ```
   google.api_core.exceptions.PermissionDenied
   ```
   **Solution**: Ensure service account has proper roles

3. **Project Not Found**
   ```
   google.api_core.exceptions.NotFound
   ```
   **Solution**: Verify project ID is correct

4. **Rate Limiting**
   ```
   google.api_core.exceptions.ResourceExhausted
   ```
   **Solution**: Implement exponential backoff in your code

### Testing

Run the example script to test your setup:

```bash
python examples/firestore_example.py
```

Run the tests:

```bash
pytest tests/test_firestore_integration.py
```

## Example Configuration

Create a configuration file `config.py`:

```python
import os

# Firestore Configuration
FIRESTORE_CONFIG = {
    'project_id': os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'your-project-id'),
    'price_collection': 'price_data',
    'trade_collection': 'trades'
}

# Trading Configuration
TRADING_CONFIG = {
    'symbols': ['bitcoin', 'ethereum', 'cardano'],
    'interval': 60,  # seconds
    'strategy': {
        'type': 'SMA_CROSS',
        'short_window': 5,
        'long_window': 20
    }
}
```

## Monitoring

Set up monitoring in Google Cloud Console:

1. **Firestore Dashboard**: Monitor read/write operations
2. **Logging**: View application logs
3. **Billing**: Set up budget alerts
4. **Error Reporting**: Monitor application errors

## Next Steps

1. Set up your Google Cloud project and Firestore database
2. Configure authentication
3. Run the example script to test the setup
4. Integrate with your trading bot
5. Monitor usage and costs
6. Set up automated backups if needed 