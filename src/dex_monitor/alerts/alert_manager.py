"""Alert management system for DEX monitoring."""

import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict, deque

from ..core.models import (
    Alert, DepegAlert, VolumeAlert, SwapEvent, LiquidityEvent, 
    PriceData, Token, TradingPair, AlertSeverity, EventType
)
from ..core.config import config
from ..data.database import DatabaseManager

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages alert generation, processing, and notifications."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_callbacks: List[Callable] = []
        
        # Price tracking for depeg detection
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.volume_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        
        # Configuration
        self.depeg_threshold = config.get('alerts.depeg_threshold', 0.05)
        self.price_change_threshold = config.get('alerts.price_change_threshold', 0.10)
        self.volume_spike_threshold = config.get('alerts.volume_spike_threshold', 2.0)
        
        # Alert cooldown to prevent spam
        self.alert_cooldown: Dict[str, datetime] = {}
        self.cooldown_duration = timedelta(minutes=10)
    
    def add_alert_callback(self, callback: Callable):
        """Add a callback to be called when alerts are generated."""
        self.alert_callbacks.append(callback)
    
    async def process_event(self, event: Any):
        """Process an event and generate alerts if necessary."""
        try:
            if isinstance(event, SwapEvent):
                await self._process_swap_event(event)
            elif isinstance(event, LiquidityEvent):
                await self._process_liquidity_event(event)
            elif isinstance(event, PriceData):
                await self._process_price_data(event)
        except Exception as e:
            logger.error(f"Error processing event for alerts: {e}")
    
    async def _process_swap_event(self, event: SwapEvent):
        """Process swap event for potential alerts."""
        # Track volume for volume spike detection
        pair_key = f"{event.pair.pair_name}_{event.pair.pool_address}"
        volume_usd = event.amount_in * (event.token_in.current_price or 1.0)
        
        self.volume_history[pair_key].append({
            'timestamp': event.timestamp,
            'volume': volume_usd
        })
        
        # Check for volume spikes
        await self._check_volume_spike(event.pair, volume_usd)
        
        # Check for large price movements
        if event.price > 0:
            await self._check_price_movement(event)
    
    async def _process_liquidity_event(self, event: LiquidityEvent):
        """Process liquidity event for potential alerts."""
        # Large liquidity removals could indicate issues
        if event.event_type == EventType.LIQUIDITY_REMOVE:
            liquidity_usd = abs(event.liquidity_delta)  # Simplified calculation
            
            if liquidity_usd > 1000000:  # $1M threshold
                alert = Alert(
                    id=str(uuid.uuid4()),
                    timestamp=event.timestamp,
                    event_type=EventType.LIQUIDITY_REMOVE,
                    severity=AlertSeverity.HIGH,
                    title=f"Large Liquidity Removal: {event.pair.pair_name}",
                    message=f"Large liquidity removal detected: ${liquidity_usd:,.2f} from {event.pair.pair_name}",
                    data={
                        'pair_name': event.pair.pair_name,
                        'pool_address': event.pair.pool_address,
                        'liquidity_removed': liquidity_usd,
                        'provider': event.provider
                    }
                )
                
                await self._emit_alert(alert)
    
    async def _process_price_data(self, price_data: PriceData):
        """Process price data for depeg detection."""
        token_symbol = price_data.token.symbol
        
        # Store price history
        self.price_history[token_symbol].append({
            'timestamp': price_data.timestamp,
            'price': price_data.price_usd
        })
        
        # Check for depeg scenarios (mainly for stablecoins)
        if token_symbol in ['USDC', 'USDT', 'DAI', 'FRAX']:
            await self._check_stablecoin_depeg(price_data)
        
        # Check for significant price changes
        if price_data.price_change_24h and abs(price_data.price_change_24h) > self.price_change_threshold * 100:
            severity = AlertSeverity.HIGH if abs(price_data.price_change_24h) > 20 else AlertSeverity.MEDIUM
            
            alert = Alert(
                id=str(uuid.uuid4()),
                timestamp=price_data.timestamp,
                event_type=EventType.PRICE_CHANGE,
                severity=severity,
                title=f"Significant Price Change: {token_symbol}",
                message=f"{token_symbol} price changed by {price_data.price_change_24h:.2f}% in 24h",
                data={
                    'token_symbol': token_symbol,
                    'price_change_24h': price_data.price_change_24h,
                    'current_price': price_data.price_usd,
                    'volume_24h': price_data.volume_24h
                }
            )
            
            await self._emit_alert(alert)
    
    async def _check_stablecoin_depeg(self, price_data: PriceData):
        """Check if a stablecoin has depegged from $1."""
        expected_price = 1.0
        actual_price = price_data.price_usd
        deviation = abs(actual_price - expected_price) / expected_price
        
        if deviation > self.depeg_threshold:
            # Check cooldown to prevent spam
            cooldown_key = f"depeg_{price_data.token.symbol}"
            if self._is_on_cooldown(cooldown_key):
                return
            
            # Determine severity based on deviation
            if deviation > 0.20:  # 20%
                severity = AlertSeverity.CRITICAL
            elif deviation > 0.10:  # 10%
                severity = AlertSeverity.HIGH
            else:
                severity = AlertSeverity.MEDIUM
            
            # Find a relevant trading pair for context
            relevant_pair = None
            # This is simplified - in real implementation, you'd find actual pairs
            if price_data.token.symbol == 'USDC':
                # Create a mock pair for demonstration
                from ..data.market_data import MarketDataProvider
                relevant_pair = TradingPair(
                    price_data.token,
                    Token('USDT', '0xdac17f958d2ee523a2206206994597c13d831ec7', 6, 'Tether USD'),
                    '0x3416cf6c708da44db2624d63ea0aaef7113527c6',
                    0.0001
                )
            
            if relevant_pair:
                alert = DepegAlert(
                    id=str(uuid.uuid4()),
                    timestamp=price_data.timestamp,
                    event_type=EventType.DEPEG_ALERT,
                    severity=severity,
                    title=f"Token Depeg Alert: {price_data.token.symbol}",
                    message=f"{price_data.token.symbol} has depegged by {deviation * 100:.2f}%. Expected: ${expected_price:.4f}, Actual: ${actual_price:.4f}",
                    token=price_data.token,
                    expected_price=expected_price,
                    actual_price=actual_price,
                    deviation_percent=deviation * 100,
                    pair=relevant_pair
                )
                
                await self._emit_alert(alert)
                self.alert_cooldown[cooldown_key] = datetime.utcnow()
    
    async def _check_volume_spike(self, pair: TradingPair, current_volume: float):
        """Check for volume spikes in a trading pair."""
        pair_key = f"{pair.pair_name}_{pair.pool_address}"
        volume_data = list(self.volume_history[pair_key])
        
        if len(volume_data) < 10:  # Need sufficient history
            return
        
        # Calculate average volume (excluding current)
        recent_volumes = [v['volume'] for v in volume_data[-10:-1]]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        
        if avg_volume > 0 and current_volume > avg_volume * self.volume_spike_threshold:
            cooldown_key = f"volume_spike_{pair.pool_address}"
            if self._is_on_cooldown(cooldown_key):
                return
            
            spike_multiplier = current_volume / avg_volume
            severity = AlertSeverity.HIGH if spike_multiplier > 5 else AlertSeverity.MEDIUM
            
            alert = VolumeAlert(
                id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                event_type=EventType.VOLUME_SPIKE,
                severity=severity,
                title=f"Volume Spike Alert: {pair.pair_name}",
                message=f"Volume spike detected in {pair.pair_name}. Current: ${current_volume:,.2f}, Average: ${avg_volume:,.2f} ({spike_multiplier:.1f}x normal)",
                pair=pair,
                current_volume=current_volume,
                average_volume=avg_volume,
                spike_multiplier=spike_multiplier
            )
            
            await self._emit_alert(alert)
            self.alert_cooldown[cooldown_key] = datetime.utcnow()
    
    async def _check_price_movement(self, swap_event: SwapEvent):
        """Check for unusual price movements in swaps."""
        # This is a simplified implementation
        # In reality, you'd compare against external price feeds
        pass
    
    def _is_on_cooldown(self, key: str) -> bool:
        """Check if an alert type is on cooldown."""
        if key not in self.alert_cooldown:
            return False
        
        return datetime.utcnow() - self.alert_cooldown[key] < self.cooldown_duration
    
    async def _emit_alert(self, alert: Alert):
        """Emit an alert to all registered callbacks and store in database."""
        # Store in memory
        self.active_alerts[alert.id] = alert
        
        # Store in database
        self.db_manager.insert_alert(alert)
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
        
        logger.info(f"Alert generated: {alert.title} ({alert.severity.value})")
    
    async def resolve_alert(self, alert_id: str):
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolve()
            
            # Update in database
            self.db_manager.insert_alert(alert)
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert resolved: {alert.title}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_stats(self) -> Dict[str, int]:
        """Get alert statistics."""
        stats = {
            'total_active': len(self.active_alerts),
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for alert in self.active_alerts.values():
            stats[alert.severity.value] += 1
        
        return stats


class NotificationManager:
    """Manages alert notifications via various channels."""
    
    def __init__(self):
        self.email_enabled = config.get('alerts.email.enabled', False)
        self.webhook_enabled = config.get('alerts.webhook.enabled', True)
        self.webhook_urls = config.get('alerts.webhook.urls', [])
    
    async def send_notification(self, alert: Alert):
        """Send notification for an alert."""
        try:
            if self.webhook_enabled and self.webhook_urls:
                await self._send_webhook_notification(alert)
            
            if self.email_enabled:
                await self._send_email_notification(alert)
                
        except Exception as e:
            logger.error(f"Error sending notification for alert {alert.id}: {e}")
    
    async def _send_webhook_notification(self, alert: Alert):
        """Send webhook notification."""
        payload = {
            'id': alert.id,
            'timestamp': alert.timestamp.isoformat(),
            'event_type': alert.event_type.value,
            'severity': alert.severity.value,
            'title': alert.title,
            'message': alert.message,
            'data': alert.data
        }
        
        # In a real implementation, you would send HTTP POST requests to webhook URLs
        logger.info(f"Webhook notification sent for alert: {alert.title}")
    
    async def _send_email_notification(self, alert: Alert):
        """Send email notification."""
        # In a real implementation, you would send emails using SMTP
        logger.info(f"Email notification sent for alert: {alert.title}")