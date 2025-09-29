"""Utility functions for the DEX monitoring system."""

import hashlib
import time
from datetime import datetime
from typing import Dict, Any, Optional


def generate_event_id(event_data: Dict[str, Any]) -> str:
    """Generate a unique ID for an event based on its data."""
    # Create a string representation of key event data
    key_data = f"{event_data.get('timestamp', '')}{event_data.get('transaction_hash', '')}{event_data.get('block_number', '')}"
    
    # Generate SHA256 hash
    return hashlib.sha256(key_data.encode()).hexdigest()[:16]


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values."""
    if old_value == 0:
        return 0.0 if new_value == 0 else float('inf')
    
    return ((new_value - old_value) / old_value) * 100


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount for display."""
    if currency == "USD":
        if amount >= 1_000_000:
            return f"${amount/1_000_000:.2f}M"
        elif amount >= 1_000:
            return f"${amount/1_000:.2f}K"
        else:
            return f"${amount:.2f}"
    else:
        return f"{amount:.6f} {currency}"


def format_time_ago(timestamp: datetime) -> str:
    """Format a timestamp as 'time ago' string."""
    now = datetime.utcnow()
    diff = now - timestamp
    
    seconds = int(diff.total_seconds())
    
    if seconds < 60:
        return f"{seconds}s ago"
    elif seconds < 3600:
        return f"{seconds // 60}m ago"
    elif seconds < 86400:
        return f"{seconds // 3600}h ago"
    else:
        return f"{seconds // 86400}d ago"


def validate_ethereum_address(address: str) -> bool:
    """Validate if a string is a valid Ethereum address."""
    if not address.startswith('0x'):
        return False
    
    if len(address) != 42:
        return False
    
    try:
        int(address[2:], 16)
        return True
    except ValueError:
        return False


def calculate_slippage(expected_amount: float, actual_amount: float) -> float:
    """Calculate slippage percentage."""
    if expected_amount == 0:
        return 0.0
    
    return abs((actual_amount - expected_amount) / expected_amount) * 100


def is_stablecoin(token_symbol: str) -> bool:
    """Check if a token is considered a stablecoin."""
    stablecoins = {'USDC', 'USDT', 'DAI', 'BUSD', 'FRAX', 'LUSD', 'MIM', 'TUSD'}
    return token_symbol.upper() in stablecoins


def get_risk_level(deviation_percent: float) -> str:
    """Get risk level based on deviation percentage."""
    if deviation_percent >= 20:
        return "CRITICAL"
    elif deviation_percent >= 10:
        return "HIGH"
    elif deviation_percent >= 5:
        return "MEDIUM"
    else:
        return "LOW"


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_make_call(self) -> bool:
        """Check if a call can be made without exceeding rate limit."""
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        return len(self.calls) < self.max_calls
    
    def make_call(self) -> bool:
        """Make a call if rate limit allows."""
        if self.can_make_call():
            self.calls.append(time.time())
            return True
        return False
    
    def get_wait_time(self) -> float:
        """Get time to wait before next call can be made."""
        if not self.calls:
            return 0.0
        
        now = time.time()
        oldest_call = min(self.calls)
        
        return max(0, self.time_window - (now - oldest_call))