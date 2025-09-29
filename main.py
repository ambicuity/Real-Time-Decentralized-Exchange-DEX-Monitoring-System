#!/usr/bin/env python3
"""
DEX Monitoring System Main Entry Point

This script starts the complete DEX monitoring system including:
- Real-time event simulation and monitoring
- Alert system for depeg and anomaly detection
- Web dashboard for visualization
- Data persistence and management
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from dex_monitor.core.monitor import main

if __name__ == "__main__":
    print("🚀 Starting DEX Monitoring System...")
    print("=" * 50)
    print("Real-Time Decentralized Exchange Monitoring")
    print("Features:")
    print("- Smart contract event monitoring")
    print("- Token depeg detection")
    print("- Volume spike alerts")
    print("- Real-time dashboard")
    print("- Market data simulation")
    print("=" * 50)
    print()
    print("Dashboard will be available at: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the system")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 DEX Monitoring System stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)