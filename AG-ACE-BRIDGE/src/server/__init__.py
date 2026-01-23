"""
Server module for AG-ACE-BRIDGE

Provides web server components:
- Dashboard: Real-time monitoring UI
- API: REST API for control and status
"""

from .dashboard import app, run_dashboard

__all__ = ["app", "run_dashboard"]
