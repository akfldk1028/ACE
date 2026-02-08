"""Tests for AG-ACE-BRIDGE shared memory client module."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.memory.shared_memory_client import SharedMemoryClient


class TestSharedMemoryClient:
    """Tests for SharedMemoryClient class."""

    def test_client_creation(self):
        """Should create SharedMemoryClient instance."""
        client = SharedMemoryClient()
        assert client is not None

    def test_client_has_base_url(self):
        """Client should have base URL."""
        client = SharedMemoryClient()
        assert hasattr(client, 'base_url') or hasattr(client, 'url')


class TestSharedMemoryClientMethods:
    """Tests for client methods."""

    def test_has_store_method(self):
        """Should have store method."""
        client = SharedMemoryClient()
        methods = dir(client)
        store_methods = [m for m in methods if 'store' in m.lower()]
        assert len(store_methods) > 0

    def test_has_get_method(self):
        """Should have get or retrieve method."""
        client = SharedMemoryClient()
        methods = dir(client)
        get_methods = [m for m in methods if 'get' in m.lower() or 'retrieve' in m.lower()]
        assert len(get_methods) > 0


class TestSharedMemoryClientIntegration:
    """Integration tests requiring server."""

    @pytest.mark.skip(reason="Requires SharedMemory server at :8101")
    def test_store_and_retrieve(self):
        """Should store and retrieve data."""
        pass

    @pytest.mark.skip(reason="Requires SharedMemory server at :8101")
    def test_health_check(self):
        """Should check server health."""
        pass
