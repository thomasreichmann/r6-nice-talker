import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.bot import AutoChatBot
from src.events import EventBus, Event, EventType
from src.interfaces import IMessageProvider, IChatTyper, IContextObserver

@pytest.fixture
def mock_provider():
    provider = MagicMock(spec=IMessageProvider)
    provider.get_message = AsyncMock(return_value="test message")
    return provider

@pytest.fixture
def mock_typer():
    typer = MagicMock(spec=IChatTyper)
    typer.send = AsyncMock()
    return typer

@pytest.fixture
def mock_event_bus():
    # We mock EventBus because we don't want actual async queue logic in unit test of bot
    # But AutoChatBot expects an EventBus instance. 
    # We can pass a real EventBus or a mock. 
    # Since we want to trigger events manually without full loop, a Mock is safer for unit testing logic.
    bus = AsyncMock(spec=EventBus)
    bus.get = AsyncMock()
    return bus

@pytest.fixture
def mock_context_observer():
    observer = MagicMock(spec=IContextObserver)
    observer.get_context = MagicMock(return_value="Vision Context")
    return observer

@pytest.mark.asyncio
async def test_process_trigger_chat(mock_provider, mock_typer, mock_event_bus):
    """
    Test that _process_trigger_chat retrieves a message and types it.
    """
    bot = AutoChatBot(
        trigger_key="f1",
        voice_trigger_key="f2",
        message_provider=mock_provider,
        chat_typer=mock_typer,
        event_bus=mock_event_bus
    )
    
    # Mock SoundManager to avoid playing actual sounds
    with patch("src.bot.SoundManager"):
        await bot._process_trigger_chat()
    
    mock_provider.get_message.assert_called_once()
    mock_typer.send.assert_called_once_with("test message")

@pytest.mark.asyncio
async def test_process_trigger_chat_with_context(mock_provider, mock_typer, mock_event_bus, mock_context_observer):
    """
    Test that visual context is passed to the provider if observer is present.
    """
    bot = AutoChatBot(
        trigger_key="f1",
        voice_trigger_key="f2",
        message_provider=mock_provider,
        chat_typer=mock_typer,
        event_bus=mock_event_bus,
        context_observer=mock_context_observer
    )
    
    with patch("src.bot.SoundManager"):
        await bot._process_trigger_chat()
    
    # Check if context_override was passed
    mock_provider.get_message.assert_called_once_with(mode="text", context_override="Vision Context")
    mock_typer.send.assert_called_once()

@pytest.mark.asyncio
async def test_callbacks_publish_events(mock_provider, mock_typer, mock_event_bus):
    """
    Test that hotkey callbacks publish the correct events to the bus.
    """
    bot = AutoChatBot(
        trigger_key="f1",
        voice_trigger_key="f2",
        message_provider=mock_provider,
        chat_typer=mock_typer,
        event_bus=mock_event_bus
    )
    
    bot._trigger_chat_callback()
    # Verify publish was called with correct event type
    # Since we passed a mock event bus, we check the mock
    args, _ = mock_event_bus.publish.call_args
    event = args[0]
    assert event.type == EventType.TRIGGER_CHAT

    bot._trigger_voice_callback()
    args, _ = mock_event_bus.publish.call_args
    event = args[0]
    assert event.type == EventType.TRIGGER_VOICE

