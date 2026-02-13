import json
import logging
import asyncio
from typing import Any, Optional

from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)

CHANNEL_TOPOLOGY = "topology_updates"
CHANNEL_ALERTS = "alert_updates"
CHANNEL_SCANS = "scan_updates"


class EventBus:
    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Store the main asyncio event loop for thread-safe broadcasts."""
        self._loop = loop

    def publish_device_update(self, event_type: str, device_data: dict):
        message = {"type": event_type, "data": device_data}
        redis_client.publish(CHANNEL_TOPOLOGY, message)
        self._notify_ws(message)

    def publish_connection_change(self, connection_data: dict):
        message = {"type": "connection_change", "data": connection_data}
        redis_client.publish(CHANNEL_TOPOLOGY, message)
        self._notify_ws(message)

    def publish_alert(self, alert_data: dict):
        message = {"type": "alert", "data": alert_data}
        redis_client.publish(CHANNEL_ALERTS, message)
        self._notify_ws(message)

    def publish_scan_progress(self, progress_data: dict):
        message = {"type": "scan_progress", "data": progress_data}
        redis_client.publish(CHANNEL_SCANS, message)
        self._notify_ws(message)

    def _notify_ws(self, message: dict):
        from app.services.realtime.ws_manager import ws_manager
        try:
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    ws_manager.broadcast(message), self._loop
                )
            else:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(ws_manager.broadcast(message))
                else:
                    loop.run_until_complete(ws_manager.broadcast(message))
        except RuntimeError:
            pass


event_bus = EventBus()
