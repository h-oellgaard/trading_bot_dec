import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Mock Firestore for testing
with patch.dict('sys.modules', {
    'google.cloud': MagicMock(),
    'google.cloud.firestore': MagicMock()
}):
    from src.infrastructure.firestore_repository import (
        FirestorePriceDataRepository, 
        FirestoreTradeRepository
    )
    from src.domain.repository import PriceData, MarketData
    from src.domain.trade import Trade
    from src.domain.coin import Coin


class TestFirestorePriceDataRepository:
    """Test Firestore price data repository"""
    
    def setup_method(self):
        """Setup test fixtures"""
        with patch('src.infrastructure.firestore_repository.FIRESTORE_AVAILABLE', True):
            self.repository = FirestorePriceDataRepository(project_id='test-project')
    
    def test_save_price_data(self):
        """Test saving price data"""
        price_data = PriceData(
            symbol='bitcoin',
            price=50000.0,
            volume=1000000.0,
            timestamp=datetime.now(),
            source='test'
        )
        
        with patch.object(self.repository.db, 'batch') as mock_batch:
            result = self.repository.save_price_data(price_data)
            assert result is True
    
    def test_get_latest_price(self):
        """Test getting latest price"""
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            'symbol': 'bitcoin',
            'price': 50000.0,
            'volume': 1000000.0,
            'timestamp': datetime.now(),
            'source': 'test'
        }
        
        with patch.object(self.repository.collection, 'where') as mock_where:
            mock_where.return_value.order_by.return_value.limit.return_value.stream.return_value = [mock_doc]
            
            result = self.repository.get_latest_price('bitcoin')
            assert result is not None
            assert result.symbol == 'bitcoin'
            assert result.price == 50000.0
    
    def test_get_market_data(self):
        """Test getting market data"""
        mock_docs = []
        for i in range(5):
            mock_doc = MagicMock()
            mock_doc.to_dict.return_value = {
                'symbol': 'bitcoin',
                'price': 50000.0 + i,
                'volume': 1000000.0,
                'timestamp': datetime.now() + timedelta(minutes=i),
                'source': 'test'
            }
            mock_docs.append(mock_doc)
        
        with patch.object(self.repository.collection, 'where') as mock_where:
            mock_where.return_value.order_by.return_value.limit.return_value.stream.return_value = mock_docs
            
            result = self.repository.get_market_data('bitcoin', 5)
            assert result is not None
            assert len(result) == 5
            assert result.symbol == 'bitcoin'


class TestFirestoreTradeRepository:
    """Test Firestore trade repository"""
    
    def setup_method(self):
        """Setup test fixtures"""
        with patch('src.infrastructure.firestore_repository.FIRESTORE_AVAILABLE', True):
            self.repository = FirestoreTradeRepository(project_id='test-project')
    
    def test_save_trade(self):
        """Test saving trade"""
        coin = Coin(symbol='bitcoin', name='Bitcoin', precision=8)
        trade = Trade(
            coin=coin,
            action='BUY',
            amount=0.1,
            price=50000.0,
            timestamp=datetime.now(),
            strategy='SMA_CROSS'
        )
        
        with patch.object(self.repository.collection, 'document') as mock_doc:
            result = self.repository.save_trade(trade)
            assert result is True
    
    def test_get_trades(self):
        """Test getting trades"""
        mock_docs = []
        for i in range(3):
            mock_doc = MagicMock()
            mock_doc.id = f'trade_{i}'
            mock_doc.to_dict.return_value = {
                'symbol': 'bitcoin',
                'action': 'BUY',
                'amount': 0.1,
                'price': 50000.0 + i * 1000,
                'timestamp': datetime.now() - timedelta(hours=i),
                'strategy': 'SMA_CROSS',
                'status': 'PENDING'
            }
            mock_docs.append(mock_doc)
        
        with patch.object(self.repository.collection, 'where') as mock_where:
            mock_where.return_value.order_by.return_value.limit.return_value.stream.return_value = mock_docs
            
            result = self.repository.get_trades(symbol='bitcoin', limit=3)
            assert len(result) == 3
            assert all(trade.coin.symbol == 'bitcoin' for trade in result)
    
    def test_get_trading_statistics(self):
        """Test getting trading statistics"""
        # Mock trades
        mock_docs = []
        for i in range(5):
            mock_doc = MagicMock()
            mock_doc.to_dict.return_value = {
                'symbol': 'bitcoin',
                'action': 'BUY' if i % 2 == 0 else 'SELL',
                'amount': 0.1,
                'price': 50000.0,
                'timestamp': datetime.now() - timedelta(hours=i),
                'strategy': 'SMA_CROSS',
                'status': 'PENDING'
            }
            mock_docs.append(mock_doc)
        
        with patch.object(self.repository.collection, 'where') as mock_where:
            mock_where.return_value.order_by.return_value.limit.return_value.stream.return_value = mock_docs
            
            result = self.repository.get_trading_statistics(symbol='bitcoin')
            assert result['total_trades'] == 5
            assert result['buy_trades'] == 3  # 0, 2, 4 are BUY
            assert result['sell_trades'] == 2  # 1, 3 are SELL


class TestDataManagerIntegration:
    """Test DataManager integration with Firestore"""
    
    def setup_method(self):
        """Setup test fixtures"""
        with patch('src.data_manager.FirestorePriceDataRepository') as mock_price_repo, \
             patch('src.data_manager.FirestoreTradeRepository') as mock_trade_repo, \
             patch('src.data_manager.DataService') as mock_data_service:
            
            self.mock_price_repo = mock_price_repo.return_value
            self.mock_trade_repo = mock_trade_repo.return_value
            self.mock_data_service = mock_data_service.return_value
            
            from src.data_manager import DataManager
            self.data_manager = DataManager(project_id='test-project')
    
    def test_get_market_data_from_firestore(self):
        """Test getting market data from Firestore"""
        # Mock Firestore response
        mock_market_data = MarketData(
            symbol='bitcoin',
            prices=[50000.0, 51000.0, 52000.0],
            volumes=[1000000.0, 1100000.0, 1200000.0],
            timestamps=[datetime.now() - timedelta(minutes=2), 
                       datetime.now() - timedelta(minutes=1), 
                       datetime.now()]
        )
        
        self.mock_price_repo.get_market_data.return_value = mock_market_data
        
        result = self.data_manager.get_market_data('bitcoin', 3)
        
        assert result is not None
        assert len(result) == 3
        assert result.symbol == 'bitcoin'
        self.mock_price_repo.get_market_data.assert_called_once_with('bitcoin', 3)
    
    def test_save_trade_to_firestore(self):
        """Test saving trade to Firestore"""
        coin = Coin(symbol='bitcoin', name='Bitcoin', precision=8)
        trade = Trade(
            coin=coin,
            action='BUY',
            amount=0.1,
            price=50000.0,
            timestamp=datetime.now(),
            strategy='SMA_CROSS'
        )
        
        self.mock_trade_repo.save_trade.return_value = True
        
        result = self.data_manager.save_trade(trade)
        
        assert result is True
        self.mock_trade_repo.save_trade.assert_called_once_with(trade)
    
    def test_get_trading_statistics(self):
        """Test getting trading statistics"""
        mock_stats = {
            'total_trades': 10,
            'buy_trades': 6,
            'sell_trades': 4,
            'total_volume': 500000.0
        }
        
        self.mock_trade_repo.get_trading_statistics.return_value = mock_stats
        
        result = self.data_manager.get_trading_statistics(symbol='bitcoin')
        
        assert result == mock_stats
        self.mock_trade_repo.get_trading_statistics.assert_called_once_with(
            symbol='bitcoin', start_time=None, end_time=None
        )


if __name__ == "__main__":
    pytest.main([__file__]) 