import logging
import threading
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class Event:
    """Base event payload structure."""

    def __init__(self, event_name: str, payload: dict[str, Any] | None = None) -> None:
        self.event_name = event_name
        self.payload = payload or {}


class Subscriber:
    """Interface or type definition for event listeners."""

    def __init__(self, callback: Callable[[Event], None]) -> None:
        self.callback = callback

    def handle(self, event: Event) -> None:
        self.callback(event)


class EventDispatcher:
    """Lightweight, thread-safe, synchronous event broker coordinating TIE execution phases."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Event], None]]] = {}
        self._lock = threading.Lock()

    def register(self, event_name: str, subscriber_callback: Callable[[Event], None]) -> None:
        """Register an event listener callback for a specific event name."""
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            # Prevent duplicate subscriptions of the exact same callback
            if subscriber_callback not in self._subscribers[event_name]:
                self._subscribers[event_name].append(subscriber_callback)

    def unregister(self, event_name: str, subscriber_callback: Callable[[Event], None]) -> bool:
        """Unregister a callback from a specific event. Returns True if found and removed."""
        with self._lock:
            if event_name in self._subscribers and subscriber_callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(subscriber_callback)
                return True
            return False

    def publish(self, event: Event, propagate_exceptions: bool = False) -> None:
        """Trigger all registered synchronous subscribers for the given event."""
        with self._lock:
            # Create a copy of the callback list to prevent race conditions during traversal
            callbacks = list(self._subscribers.get(event.event_name, []))

        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(
                    f"Error executing subscriber for event '{event.event_name}': {e}",
                    exc_info=True
                )
                if propagate_exceptions:
                    raise e


# Global default synchronous event dispatcher instance
dispatcher = EventDispatcher()

