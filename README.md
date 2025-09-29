# Real-Time DEX Monitoring System

🚀 **A comprehensive real-time monitoring system for decentralized exchanges (DEX) that tracks smart contract events, market changes, and provides intelligent alerts for potential token depeg scenarios and protocol updates.**

## 🌟 Features

### 📊 Real-Time Monitoring
- **Smart Contract Event Tracking**: Monitor swap, liquidity, and protocol events
- **Market Data Ingestion**: Real-time price and volume data processing
- **Multi-DEX Support**: Extensible architecture for different DEX protocols

### 🚨 Intelligent Alerting
- **Token Depeg Detection**: Advanced algorithms to detect stablecoin depegging
- **Volume Spike Alerts**: Identify unusual trading activity patterns  
- **Price Movement Monitoring**: Track significant price changes across assets
- **Protocol Update Notifications**: Monitor for critical protocol changes

### 📈 Interactive Dashboard
- **Real-Time Visualization**: Live charts and metrics updates
- **Alert Management**: View, filter, and resolve alerts
- **Historical Data**: Price history and trading activity analysis
- **Responsive Design**: Mobile-friendly web interface

### 🔧 Technical Infrastructure
- **Streaming Data Pipeline**: Asynchronous Python-based data processing
- **Database Storage**: SQLite with configurable retention policies
- **WebSocket Communication**: Real-time updates to dashboard
- **Configurable Parameters**: Flexible monitoring thresholds and settings

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Market Data   │    │   Event Stream   │    │  Alert System   │
│   Providers     │───▶│   Processor      │───▶│   & Notifier    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │    Database      │    │   Dashboard     │
                       │    Storage       │    │   Interface     │
                       └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ambicuity/Real-Time-Decentralized-Exchange-DEX-Monitoring-System.git
cd Real-Time-Decentralized-Exchange-DEX-Monitoring-System
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the monitoring system**
```bash
python main.py
```

5. **Access the dashboard**
Open your browser and navigate to: `http://127.0.0.1:5000`

## 📋 Configuration

The system uses `config/config.yaml` for configuration. Key settings include:

### Alert Thresholds
```yaml
alerts:
  depeg_threshold: 0.05      # 5% deviation threshold
  price_change_threshold: 0.10  # 10% price change threshold
  volume_spike_threshold: 2.0   # 2x normal volume
```

### Dashboard Settings
```yaml
dashboard:
  host: "127.0.0.1"
  port: 5000
  update_interval: 5  # seconds
```

### Monitoring Parameters
```yaml
monitoring:
  poll_interval: 10        # seconds
  data_retention_days: 30  # days
```

## 🎯 Use Cases

### DeFi Protocol Monitoring
- **Risk Management**: Early detection of market anomalies and liquidity issues
- **Operational Oversight**: Monitor protocol health and user activity
- **Compliance**: Track large transactions and unusual patterns

### Trading and Investment
- **Market Intelligence**: Real-time insights into DEX activity and trends  
- **Risk Assessment**: Identify potential depeg events before they escalate
- **Opportunity Detection**: Spot volume spikes and arbitrage opportunities

### Research and Analytics
- **Market Analysis**: Historical data for research and backtesting
- **Protocol Comparison**: Compare activity across different DEX platforms
- **Trend Identification**: Long-term market pattern analysis

## 🔧 System Components

### Core Modules

#### `src/dex_monitor/core/`
- **`config.py`**: Configuration management
- **`models.py`**: Data models and schemas
- **`monitor.py`**: Main system coordinator

#### `src/dex_monitor/data/`
- **`database.py`**: Data persistence layer
- **`market_data.py`**: Market data ingestion and simulation

#### `src/dex_monitor/alerts/`
- **`alert_manager.py`**: Alert generation and management
- **`notification.py`**: Multi-channel notification system

#### `src/dex_monitor/dashboard/`
- **`app.py`**: Web dashboard application
- **`templates/`**: HTML templates
- **`static/`**: CSS, JavaScript, and assets

## 📊 Dashboard Features

### Real-Time Metrics
- Active alerts count with severity breakdown
- Recent swap activity (1-hour window)
- Total trading volume statistics
- Number of monitored trading pairs

### Interactive Charts
- Token price history with customizable timeframes
- Volume trends and spike detection
- Alert frequency and resolution metrics

### Alert Management
- View active and resolved alerts
- Filter by severity and time period
- One-click alert resolution
- Real-time alert notifications

## 🚨 Alert Types

### Depeg Alerts
Triggered when stablecoins deviate significantly from their peg:
- **Critical**: >20% deviation
- **High**: 10-20% deviation  
- **Medium**: 5-10% deviation

### Volume Spikes
Detected when trading volume exceeds normal patterns:
- **High**: >5x normal volume
- **Medium**: 2-5x normal volume

### Price Movements
Large price changes in short timeframes:
- **Critical**: >20% change in 24h
- **High**: 10-20% change in 24h
- **Medium**: 5-10% change in 24h

## 🔧 Development Setup

### Running Tests
```bash
pip install pytest pytest-asyncio
pytest tests/
```

### Code Quality
```bash
pip install black flake8 mypy
black src/
flake8 src/
mypy src/
```

### Development Mode
```bash
export FLASK_ENV=development
python main.py
```

## 📚 API Documentation

### REST Endpoints

#### System Statistics
```
GET /api/stats
```
Returns current system metrics and alert counts.

#### Alert Management
```
GET /api/alerts?hours=24&resolved=false
POST /api/resolve-alert/<alert_id>
```

#### Market Data
```
GET /api/price-history/<token_symbol>?hours=24
GET /api/swap-events?hours=24&pool_address=<address>
```

### WebSocket Events

#### Real-time Updates
- `new_alert`: New alert generated
- `alert_resolved`: Alert marked as resolved
- `new_swap`: New swap event detected
- `price_update`: Token price updated

## 🛠️ Customization

### Adding New DEX Protocols
1. Extend `MarketDataProvider` with new protocol adapters
2. Update token and pair configurations
3. Implement protocol-specific event parsing

### Custom Alert Rules
1. Create new alert classes inheriting from `Alert`
2. Add detection logic to `AlertManager`
3. Configure thresholds in `config.yaml`

### Dashboard Customization
1. Modify `templates/dashboard.html` for UI changes
2. Add new API endpoints in `dashboard/app.py`
3. Extend real-time event handling

## 🔒 Security Considerations

### Data Protection
- SQLite database with configurable retention
- No sensitive credentials stored in configuration
- Rate limiting for API endpoints

### Network Security
- WebSocket connections with CORS protection
- Input validation for all API endpoints
- Configurable host and port binding

## 📈 Performance

### System Requirements
- **Memory**: ~100MB base usage
- **CPU**: Low usage with event-driven architecture
- **Storage**: Configurable with automatic cleanup
- **Network**: Minimal bandwidth for simulated data

### Scalability Features
- Asynchronous processing for high throughput
- Database indexing for fast queries
- WebSocket broadcasting for real-time updates
- Modular architecture for easy extension

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation for new features
- Use type hints for better code clarity

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python asyncio for high-performance monitoring
- Uses Flask and SocketIO for real-time web interface  
- Plotly.js for interactive charting
- Bootstrap for responsive UI design

## 📞 Support

For questions, issues, or contributions:
- 📧 Email: team@dexmonitor.dev
- 🐛 Issues: GitHub Issues page
- 💬 Discussions: GitHub Discussions

---

**Built with ❤️ for the DeFi community**