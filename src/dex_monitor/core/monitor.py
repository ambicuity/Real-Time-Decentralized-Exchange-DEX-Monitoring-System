"""Main monitoring system coordinator."""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Optional
import threading

from .config import config
from .models import MonitoringStats
from ..data.database import DatabaseManager
from ..data.market_data import MarketDataProvider, DEXEventSimulator
from ..alerts.alert_manager import AlertManager, NotificationManager
from ..dashboard.app import DashboardApp

logger = logging.getLogger(__name__)


class DEXMonitor:
    """Main DEX monitoring system coordinator."""
    
    def __init__(self):
        """Initialize the DEX monitoring system."""
        self.running = False
        self.start_time: Optional[datetime] = None
        
        # Initialize core components
        self.db_manager = DatabaseManager()
        self.market_data_provider = MarketDataProvider(self.db_manager)
        self.event_simulator = DEXEventSimulator(self.market_data_provider, self.db_manager)
        self.alert_manager = AlertManager(self.db_manager)
        self.notification_manager = NotificationManager()
        self.dashboard_app = DashboardApp(self.db_manager)
        
        # Statistics tracking
        self.total_events_processed = 0
        self.last_stats_update = datetime.utcnow()
        
        # Setup event callbacks
        self._setup_event_callbacks()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_event_callbacks(self):
        """Setup callbacks between components."""
        # Market data events go to alert manager
        self.event_simulator.add_event_callback(self._process_event)
        
        # Alerts go to notification manager and dashboard
        self.alert_manager.add_alert_callback(self._handle_alert)
    
    async def _process_event(self, event):
        """Process an event through the alert system."""
        try:
            await self.alert_manager.process_event(event)
            self.total_events_processed += 1
            
            # Broadcast to dashboard
            if hasattr(event, 'pair') and hasattr(event, 'amount_in'):  # SwapEvent
                self.dashboard_app.broadcast_swap_event(event)
                
        except Exception as e:
            logger.error(f"Error processing event: {e}")
    
    async def _handle_alert(self, alert):
        """Handle a new alert."""
        try:
            # Send notification
            await self.notification_manager.send_notification(alert)
            
            # Broadcast to dashboard
            self.dashboard_app.broadcast_alert(alert)
            
        except Exception as e:
            logger.error(f"Error handling alert: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    async def start(self):
        """Start the monitoring system."""
        if self.running:
            logger.warning("Monitor is already running")
            return
        
        self.running = True
        self.start_time = datetime.utcnow()
        
        logger.info("Starting DEX monitoring system...")
        
        try:
            # Start market data provider
            await self.market_data_provider.start()
            
            # Start the monitoring tasks
            monitoring_tasks = [
                asyncio.create_task(self.event_simulator.start_simulation()),
                asyncio.create_task(self._stats_updater()),
                asyncio.create_task(self._cleanup_task())
            ]
            
            # Start dashboard in a separate thread
            dashboard_thread = threading.Thread(
                target=self.dashboard_app.run,
                daemon=True
            )
            dashboard_thread.start()
            
            logger.info("DEX monitoring system started successfully")
            
            # Wait for all tasks to complete
            await asyncio.gather(*monitoring_tasks)
            
        except Exception as e:
            logger.error(f"Error starting monitoring system: {e}")
            raise
        finally:
            await self._cleanup()
    
    def stop(self):
        """Stop the monitoring system."""
        logger.info("Stopping DEX monitoring system...")
        self.running = False
        self.event_simulator.stop_simulation()
    
    async def _stats_updater(self):
        """Periodically update monitoring statistics."""
        while self.running:
            try:
                await asyncio.sleep(60)  # Update stats every minute
                
                if not self.running:
                    break
                
                # Calculate uptime
                uptime_seconds = int((datetime.utcnow() - self.start_time).total_seconds())
                
                # Calculate events per minute
                time_diff = (datetime.utcnow() - self.last_stats_update).total_seconds() / 60
                events_per_minute = self.total_events_processed / max(time_diff, 1)
                
                # Get active alerts count
                active_alerts = len(self.alert_manager.get_active_alerts())
                
                # Create stats object
                stats = MonitoringStats(
                    timestamp=datetime.utcnow(),
                    total_pairs_monitored=len(self.market_data_provider.trading_pairs),
                    total_events_processed=self.total_events_processed,
                    active_alerts=active_alerts,
                    uptime_seconds=uptime_seconds,
                    last_block_processed=self.event_simulator.current_block,
                    events_per_minute=events_per_minute
                )
                
                # Store in database
                self.db_manager.insert_monitoring_stats(stats)
                
                logger.debug(f"Stats updated: {self.total_events_processed} events, "
                           f"{active_alerts} alerts, {uptime_seconds}s uptime")
                
            except Exception as e:
                logger.error(f"Error updating stats: {e}")
    
    async def _cleanup_task(self):
        """Periodic cleanup of old data."""
        while self.running:
            try:
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
                if not self.running:
                    break
                
                # Clean up old data
                retention_days = config.get('monitoring.data_retention_days', 30)
                self.db_manager.cleanup_old_data(retention_days)
                
                logger.info(f"Cleaned up data older than {retention_days} days")
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def _cleanup(self):
        """Cleanup resources."""
        try:
            await self.market_data_provider.stop()
            logger.info("DEX monitoring system stopped")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/dex_monitor.log')
        ]
    )
    
    # Reduce noise from some libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)


async def main():
    """Main entry point."""
    # Setup logging
    setup_logging()
    
    logger.info("Initializing DEX monitoring system...")
    
    # Create and start monitor
    monitor = DEXMonitor()
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())