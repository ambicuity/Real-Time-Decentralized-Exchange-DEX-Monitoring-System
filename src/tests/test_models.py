"""Tests for core data models."""

import pytest
from datetime import datetime
from dex_monitor.core.models import (
    Token, TradingPair, SwapEvent, Alert, DepegAlert,
    EventType, AlertSeverity
)


def test_token_creation():
    """Test Token model creation and validation."""
    token = Token(
        symbol="USDC",
        address="0xA0b86a33E6441b2C30B7AdE5c3e77Eeddbfe1Fd8",
        decimals=6,
        name="USD Coin",
        current_price=1.0
    )
    
    assert token.symbol == "USDC"
    assert token.address == "0xa0b86a33e6441b2c30b7ade5c3e77eeddbfe1fd8"  # Lowercase
    assert token.decimals == 6
    assert token.current_price == 1.0


def test_trading_pair_creation():
    """Test TradingPair model creation."""
    token0 = Token("USDC", "0xa0b86a33e6441b2c30b7ade5c3e77eeddbfe1fd8", 6, "USD Coin")
    token1 = Token("WETH", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", 18, "Wrapped Ether")
    
    pair = TradingPair(
        token0=token0,
        token1=token1,
        pool_address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        fee_tier=0.0005
    )
    
    assert pair.pair_name == "USDC/WETH"
    assert pair.fee_tier == 0.0005
    assert pair.pool_address == "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"


def test_swap_event_creation():
    """Test SwapEvent model creation."""
    token0 = Token("USDC", "0xa0b86a33e6441b2c30b7ade5c3e77eeddbfe1fd8", 6, "USD Coin")
    token1 = Token("WETH", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", 18, "Wrapped Ether")
    pair = TradingPair(token0, token1, "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", 0.0005)
    
    swap = SwapEvent(
        timestamp=datetime.utcnow(),
        pair=pair,
        amount_in=1000.0,
        amount_out=0.4,
        token_in=token0,
        token_out=token1,
        price=2500.0,
        transaction_hash="0x123456789abcdef",
        block_number=18500000
    )
    
    assert swap.amount_in == 1000.0
    assert swap.amount_out == 0.4
    assert swap.token_in.symbol == "USDC"
    assert swap.token_out.symbol == "WETH"


def test_depeg_alert_creation():
    """Test DepegAlert model creation and auto-population."""
    token = Token("USDC", "0xa0b86a33e6441b2c30b7ade5c3e77eeddbfe1fd8", 6, "USD Coin")
    usdt = Token("USDT", "0xdac17f958d2ee523a2206206994597c13d831ec7", 6, "Tether USD")
    pair = TradingPair(token, usdt, "0x3416cf6c708da44db2624d63ea0aaef7113527c6", 0.0001)
    
    alert = DepegAlert(
        id="test-alert-1",
        timestamp=datetime.utcnow(),
        event_type=EventType.DEPEG_ALERT,
        severity=AlertSeverity.HIGH,
        title="Test Depeg Alert",
        message="Test message",
        token=token,
        expected_price=1.0,
        actual_price=0.92,
        deviation_percent=8.0,
        pair=pair
    )
    
    # Test that __post_init__ updates the fields
    alert.__post_init__()
    
    assert alert.event_type == EventType.DEPEG_ALERT
    assert alert.title == "Token Depeg Alert: USDC"
    assert "8.00%" in alert.message
    assert alert.data["deviation_percent"] == 8.0


def test_alert_resolution():
    """Test alert resolution functionality."""
    alert = Alert(
        id="test-alert",
        timestamp=datetime.utcnow(),
        event_type=EventType.PRICE_CHANGE,
        severity=AlertSeverity.MEDIUM,
        title="Test Alert",
        message="Test message"
    )
    
    assert not alert.resolved
    assert alert.resolved_at is None
    
    alert.resolve()
    
    assert alert.resolved
    assert alert.resolved_at is not None


if __name__ == "__main__":
    pytest.main([__file__])