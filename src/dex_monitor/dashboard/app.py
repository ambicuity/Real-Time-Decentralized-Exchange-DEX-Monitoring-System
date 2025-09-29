"""Web dashboard for DEX monitoring system."""

import json
import asyncio
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import logging
from typing import Dict, Any, List

from ..core.config import config
from ..data.database import DatabaseManager
from ..core.models import Alert, AlertSeverity

logger = logging.getLogger(__name__)


class DashboardApp:
    """Flask web application for the monitoring dashboard."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.app = Flask(__name__, 
                        template_folder='../../../templates',
                        static_folder='../../../static')
        self.app.config['SECRET_KEY'] = 'dex-monitoring-secret-key'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.setup_routes()
        self.setup_socketio_events()
        
        # Connected clients for real-time updates
        self.connected_clients = set()
    
    def setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            return render_template('dashboard.html')
        
        @self.app.route('/api/stats')
        def get_stats():
            """Get current system statistics."""
            try:
                # Get recent alerts
                recent_alerts = self.db_manager.get_recent_alerts(hours=24, resolved=False)
                
                # Get recent swap events
                recent_swaps = self.db_manager.get_swap_events(hours=1)
                
                # Calculate statistics
                stats = {
                    'active_alerts': len(recent_alerts),
                    'critical_alerts': len([a for a in recent_alerts if a['severity'] == 'critical']),
                    'high_alerts': len([a for a in recent_alerts if a['severity'] == 'high']),
                    'medium_alerts': len([a for a in recent_alerts if a['severity'] == 'medium']),
                    'low_alerts': len([a for a in recent_alerts if a['severity'] == 'low']),
                    'recent_swaps_1h': len(recent_swaps),
                    'total_volume_1h': sum(float(s.get('amount_in', 0)) for s in recent_swaps),
                    'monitored_pairs': 4,  # Based on our configuration
                    'last_updated': datetime.utcnow().isoformat()
                }
                
                return jsonify(stats)
                
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/alerts')
        def get_alerts():
            """Get recent alerts."""
            try:
                hours = request.args.get('hours', 24, type=int)
                resolved = request.args.get('resolved')
                
                if resolved is not None:
                    resolved = resolved.lower() == 'true'
                
                alerts = self.db_manager.get_recent_alerts(hours=hours, resolved=resolved)
                
                # Convert data field from JSON string to dict
                for alert in alerts:
                    if alert.get('data'):
                        try:
                            alert['data'] = json.loads(alert['data'])
                        except json.JSONDecodeError:
                            alert['data'] = {}
                
                return jsonify(alerts)
                
            except Exception as e:
                logger.error(f"Error getting alerts: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/price-history/<token_symbol>')
        def get_price_history(token_symbol):
            """Get price history for a token."""
            try:
                hours = request.args.get('hours', 24, type=int)
                price_data = self.db_manager.get_price_history(token_symbol, hours=hours)
                
                return jsonify(price_data)
                
            except Exception as e:
                logger.error(f"Error getting price history for {token_symbol}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/swap-events')
        def get_swap_events():
            """Get recent swap events."""
            try:
                hours = request.args.get('hours', 24, type=int)
                pool_address = request.args.get('pool_address')
                
                swap_events = self.db_manager.get_swap_events(
                    pool_address=pool_address, 
                    hours=hours
                )
                
                return jsonify(swap_events)
                
            except Exception as e:
                logger.error(f"Error getting swap events: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/resolve-alert/<alert_id>', methods=['POST'])
        def resolve_alert(alert_id):
            """Resolve an alert."""
            try:
                # Get alert from database
                alerts = self.db_manager.get_recent_alerts(hours=720)  # 30 days
                alert_data = next((a for a in alerts if a['id'] == alert_id), None)
                
                if not alert_data:
                    return jsonify({'error': 'Alert not found'}), 404
                
                # Update alert as resolved
                alert_data['resolved'] = True
                alert_data['resolved_at'] = datetime.utcnow().isoformat()
                
                # Create Alert object and update database
                alert = Alert(
                    id=alert_data['id'],
                    timestamp=datetime.fromisoformat(alert_data['timestamp']),
                    event_type=alert_data['event_type'],
                    severity=AlertSeverity(alert_data['severity']),
                    title=alert_data['title'],
                    message=alert_data['message'],
                    data=json.loads(alert_data.get('data', '{}')),
                    resolved=True,
                    resolved_at=datetime.utcnow()
                )
                
                self.db_manager.insert_alert(alert)
                
                # Notify connected clients
                self.socketio.emit('alert_resolved', {'alert_id': alert_id})
                
                return jsonify({'success': True})
                
            except Exception as e:
                logger.error(f"Error resolving alert {alert_id}: {e}")
                return jsonify({'error': str(e)}), 500
    
    def setup_socketio_events(self):
        """Setup SocketIO event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            self.connected_clients.add(request.sid)
            logger.info(f"Client connected: {request.sid}")
            emit('connected', {'status': 'Connected to DEX Monitor'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            self.connected_clients.discard(request.sid)
            logger.info(f"Client disconnected: {request.sid}")
    
    def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected clients."""
        if self.connected_clients:
            self.socketio.emit(event_type, data)
    
    def broadcast_alert(self, alert: Alert):
        """Broadcast a new alert to all connected clients."""
        alert_data = {
            'id': alert.id,
            'timestamp': alert.timestamp.isoformat(),
            'event_type': alert.event_type.value,
            'severity': alert.severity.value,
            'title': alert.title,
            'message': alert.message,
            'data': alert.data
        }
        
        self.broadcast_event('new_alert', alert_data)
    
    def broadcast_swap_event(self, swap_event):
        """Broadcast a new swap event to all connected clients."""
        event_data = {
            'timestamp': swap_event.timestamp.isoformat(),
            'pair': swap_event.pair.pair_name,
            'amount_in': swap_event.amount_in,
            'amount_out': swap_event.amount_out,
            'token_in': swap_event.token_in.symbol,
            'token_out': swap_event.token_out.symbol,
            'price': swap_event.price,
            'tx_hash': swap_event.transaction_hash[:10] + '...'
        }
        
        self.broadcast_event('new_swap', event_data)
    
    def run(self, host: str = None, port: int = None, debug: bool = None):
        """Run the Flask application."""
        if host is None:
            host = config.get('dashboard.host', '127.0.0.1')
        if port is None:
            port = config.get('dashboard.port', 5000)
        if debug is None:
            debug = config.get('dashboard.debug', True)
        
        logger.info(f"Starting dashboard at http://{host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=False, use_reloader=False)