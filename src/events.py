"""
Event system module for handling asynchronous event propagation.
"""
import asyncio
import logging
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Enumeration of all possible event types in the application."""
    TRIGGER_CHAT = auto()
    TRIGGER_VOICE = auto()
    NEXT_PERSONA = auto()
    PREV_PERSONA = auto()
    SHUTDOWN = auto()


@dataclass
class Event:
    """
    Represents an event that occurred in the system.
    
    Attributes:
        type (EventType): The type of the event.
        data (Any, optional): Additional data associated with the event.
    """
    type: EventType
    data: Optional[Any] = None


class EventBus:
    """
    Asynchronous event bus for publishing and subscribing to events.
    Uses an asyncio.Queue to buffer events for processing.
    """
    def __init__(self) -> None:
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

    def publish(self, event: Event) -> None:
        """
        Publishes an event to the bus.
        This method is thread-safe and can be called from keyboard callbacks (separate threads).
        """
        if self._loop and self._loop.is_running():
            # We are likely in a different thread (keyboard listener), so we must use call_soon_threadsafe
            self._loop.call_soon_threadsafe(self._queue.put_nowait, event)
        else:
            # Fallback if loop isn't ready or we are in a sync context (unlikely in this app structure)
            logger.warning("EventBus loop not available or not running. Event might be dropped.")

    async def get(self) -> Event:
        """
        Waits for and retrieves the next event from the queue.
        """
        return await self._queue.get()
