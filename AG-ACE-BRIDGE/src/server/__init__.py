"""
Server module for AG-ACE-BRIDGE

Provides web server components:
- Dashboard: Real-time monitoring UI
- API: REST API for control and status
- Pattern Routes: REST API for pattern management
- Project Routes: REST API for project design and execution
"""

from .dashboard import app, run_dashboard
from . import pattern_routes
from . import project_routes

__all__ = ["app", "run_dashboard", "pattern_routes", "project_routes"]
