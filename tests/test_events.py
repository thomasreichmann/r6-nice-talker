import pytest
import asyncio
from src.events import EventBus, Event, EventType

@pytest.mark.asyncio
async def test_event_bus_publish_consume():
    """
    Test that events published to the bus can be consumed.
    """
    bus = EventBus()
    # Need to set the loop explicitly because EventBus captures it in __init__
    # In pytest-asyncio, the loop is running.
    
    event = Event(EventType.TRIGGER_CHAT, "test_data")
    
    # publish uses call_soon_threadsafe which schedules it on the loop
    bus.publish(event)
    
    # consume
    consumed_event = await bus.get()
    
    assert consumed_event.type == EventType.TRIGGER_CHAT
    assert consumed_event.data == "test_data"

@pytest.mark.asyncio
async def test_event_bus_ordering():
    """
    Test that events are consumed in FIFO order.
    """
    bus = EventBus()
    
    event1 = Event(EventType.TRIGGER_CHAT, 1)
    event2 = Event(EventType.TRIGGER_VOICE, 2)
    
    bus.publish(event1)
    bus.publish(event2)
    
    consumed1 = await bus.get()
    consumed2 = await bus.get()
    
    assert consumed1.data == 1
    assert consumed2.data == 2

