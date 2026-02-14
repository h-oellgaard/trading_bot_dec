"""
Unit tests for main.py TradingBot.
Uses mocks to avoid Firebase/Firi API dependencies.
"""
import os
from unittest.mock import MagicMock, patch

import pytest


def test_poll_interval_from_env():
    """
    GIVEN POLL_INTERVAL=30 in environment
    WHEN TradingBot is initialized
    THEN bot.poll_interval is 30 seconds.
    """
    with patch.dict(os.environ, {"POLL_INTERVAL": "30"}, clear=False):
        with patch("main.FiriDataFetcher", MagicMock()):
            with patch("main.FiriTrader", MagicMock()):
                with patch("main.FirebaseStore", MagicMock()):
                    with patch("main.FirebaseLoggingHandler", MagicMock()):
                        from main import TradingBot

                        bot = TradingBot()
                        assert bot.poll_interval == 30


def test_poll_interval_custom_value():
    """
    GIVEN POLL_INTERVAL=60 in environment
    WHEN TradingBot is initialized
    THEN bot.poll_interval is 60 seconds.
    """
    with patch.dict(os.environ, {"POLL_INTERVAL": "60"}, clear=False):
        with patch("main.FiriDataFetcher", MagicMock()):
            with patch("main.FiriTrader", MagicMock()):
                with patch("main.FirebaseStore", MagicMock()):
                    with patch("main.FirebaseLoggingHandler", MagicMock()):
                        from main import TradingBot

                        bot = TradingBot()
                        assert bot.poll_interval == 60
