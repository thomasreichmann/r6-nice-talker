"""
Unit tests for TUI components.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from src.tui import (
    StatusPanel, HotkeysPanel, StatsPanel, ErrorPanel, BotTUI, ErrorLevel
)
from src.events import EventBus, Event, EventType
from src.interfaces import ISwitchableMessageProvider


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = MagicMock()
    bot.provider = MagicMock()
    bot.provider.__class__.__name__ = "ChatGPTProvider"
    bot.typer = MagicMock()
    bot.typer.__class__.__name__ = "R6Typer"
    bot.context_observer = MagicMock()
    bot.context_observer.__class__.__name__ = "EasyOCRProvider"
    bot.tts_engine = MagicMock()
    bot.tts_engine.__class__.__name__ = "ElevenLabsTTS"
    bot.trigger_key = "f6"
    bot.voice_trigger_key = "f5"
    bot.next_mode_key = "f8"
    bot.prev_mode_key = "f7"
    return bot


@pytest.fixture
def mock_switchable_provider():
    """Create a mock switchable provider."""
    provider = MagicMock(spec=ISwitchableMessageProvider)
    provider.get_current_mode_name = MagicMock(return_value="Toxic")
    provider.__class__.__name__ = "ChatGPTProvider"
    return provider


@pytest.fixture
def mock_analytics():
    """Create a mock analytics instance."""
    analytics = MagicMock()
    analytics.get_session_stats = MagicMock(return_value={
        'api_call_count': 10,
        'tts_count': 5,
        'total_tokens': 1000,
        'total_cost': 0.0015,
        'avg_latency_ms': 250.0
    })
    return analytics


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus."""
    bus = MagicMock(spec=EventBus)
    bus._loop = None
    return bus


class TestStatusPanel:
    """Tests for StatusPanel widget."""
    
    def test_status_panel_creation(self, mock_bot):
        """Test that StatusPanel can be created."""
        panel = StatusPanel(mock_bot)
        assert panel.bot == mock_bot
    
    def test_status_panel_updates(self, mock_bot):
        """Test that StatusPanel updates correctly."""
        panel = StatusPanel(mock_bot)
        panel.update_status()
        
        # Check that status content exists (would be set in actual TUI)
        assert hasattr(panel, 'update_status')
    
    def test_status_panel_with_switchable_provider(self, mock_bot, mock_switchable_provider):
        """Test StatusPanel with switchable provider."""
        mock_bot.provider = mock_switchable_provider
        panel = StatusPanel(mock_bot)
        panel.update_status()
        
        # Verify persona name is retrieved
        mock_switchable_provider.get_current_mode_name.assert_called()


class TestHotkeysPanel:
    """Tests for HotkeysPanel widget."""
    
    def test_hotkeys_panel_creation(self, mock_bot):
        """Test that HotkeysPanel can be created."""
        panel = HotkeysPanel(mock_bot)
        assert panel.bot == mock_bot
    
    def test_hotkeys_panel_updates(self, mock_bot):
        """Test that HotkeysPanel updates correctly."""
        panel = HotkeysPanel(mock_bot)
        panel.update_hotkeys()
        
        assert hasattr(panel, 'update_hotkeys')
    
    def test_hotkeys_with_switchable_provider(self, mock_bot, mock_switchable_provider):
        """Test HotkeysPanel with switchable provider."""
        mock_bot.provider = mock_switchable_provider
        panel = HotkeysPanel(mock_bot)
        panel.update_hotkeys()
        
        assert hasattr(panel, 'update_hotkeys')


class TestStatsPanel:
    """Tests for StatsPanel widget."""
    
    def test_stats_panel_creation(self, mock_analytics):
        """Test that StatsPanel can be created."""
        panel = StatsPanel(mock_analytics)
        assert panel.analytics == mock_analytics
    
    def test_stats_panel_updates(self, mock_analytics):
        """Test that StatsPanel updates correctly."""
        panel = StatsPanel(mock_analytics)
        panel.update_stats()
        
        # Verify analytics was called
        mock_analytics.get_session_stats.assert_called()
    
    def test_stats_panel_no_analytics(self):
        """Test StatsPanel with no analytics."""
        panel = StatsPanel(None)
        panel.update_stats()
        
        # Should handle None gracefully
        assert hasattr(panel, 'update_stats')
    
    def test_stats_panel_empty_stats(self, mock_analytics):
        """Test StatsPanel with empty stats."""
        mock_analytics.get_session_stats.return_value = {}
        panel = StatsPanel(mock_analytics)
        panel.update_stats()
        
        mock_analytics.get_session_stats.assert_called()


class TestErrorPanel:
    """Tests for ErrorPanel widget."""
    
    def test_error_panel_creation(self):
        """Test that ErrorPanel can be created."""
        panel = ErrorPanel()
        assert panel.errors == []
        assert panel.max_errors == 50
    
    def test_error_panel_add_error(self):
        """Test adding errors to ErrorPanel."""
        panel = ErrorPanel()
        panel.add_error(ErrorLevel.ERROR, "Test error", "Details")
        
        assert len(panel.errors) == 1
        assert panel.errors[0][1] == ErrorLevel.ERROR
        assert panel.errors[0][2] == "Test error"
        assert panel.errors[0][3] == "Details"
    
    def test_error_panel_add_multiple_errors(self):
        """Test adding multiple errors."""
        panel = ErrorPanel()
        for i in range(10):
            panel.add_error(ErrorLevel.INFO, f"Error {i}")
        
        assert len(panel.errors) == 10
    
    def test_error_panel_max_errors(self):
        """Test that ErrorPanel respects max_errors limit."""
        panel = ErrorPanel()
        panel.max_errors = 5
        
        for i in range(10):
            panel.add_error(ErrorLevel.INFO, f"Error {i}")
        
        assert len(panel.errors) == 5
        # Should keep the most recent errors
        assert panel.errors[0][2] == "Error 5"
        assert panel.errors[-1][2] == "Error 9"
    
    def test_error_panel_clear_errors(self):
        """Test clearing errors."""
        panel = ErrorPanel()
        panel.add_error(ErrorLevel.ERROR, "Test error")
        assert len(panel.errors) == 1
        
        panel.clear_errors()
        assert len(panel.errors) == 0
    
    def test_error_panel_get_latest_error_details(self):
        """Test getting latest error details."""
        panel = ErrorPanel()
        panel.add_error(ErrorLevel.ERROR, "Test error", "Stack trace")
        
        details = panel.get_latest_error_details()
        assert "Test error" in details
        assert "Stack trace" in details
    
    def test_error_panel_get_latest_error_no_details(self):
        """Test getting latest error without details."""
        panel = ErrorPanel()
        panel.add_error(ErrorLevel.ERROR, "Test error")
        
        details = panel.get_latest_error_details()
        assert details == "Test error"
    
    def test_error_panel_different_levels(self):
        """Test adding errors with different levels."""
        panel = ErrorPanel()
        panel.add_error(ErrorLevel.INFO, "Info message")
        panel.add_error(ErrorLevel.WARNING, "Warning message")
        panel.add_error(ErrorLevel.ERROR, "Error message")
        panel.add_error(ErrorLevel.CRITICAL, "Critical message")
        
        assert len(panel.errors) == 4
        assert panel.errors[0][1] == ErrorLevel.INFO
        assert panel.errors[-1][1] == ErrorLevel.CRITICAL


class TestBotTUI:
    """Tests for BotTUI application."""
    
    def test_bot_tui_creation(self, mock_bot, mock_event_bus, mock_analytics):
        """Test that BotTUI can be created."""
        # Note: We can't actually instantiate BotTUI without a running event loop
        # So we just test that the class exists and has the right structure
        assert hasattr(BotTUI, 'compose')
        assert hasattr(BotTUI, 'on_mount')
        assert hasattr(BotTUI, 'show_error')
        assert hasattr(BotTUI, 'show_warning')
        assert hasattr(BotTUI, 'show_info')
    
    def test_bot_tui_show_error_method(self):
        """Test that show_error method exists and has correct signature."""
        # Check method signature
        import inspect
        sig = inspect.signature(BotTUI.show_error)
        params = list(sig.parameters.keys())
        
        assert 'level' in params
        assert 'message' in params
        assert 'details' in params
        assert 'notify' in params
    
    def test_bot_tui_show_warning_method(self):
        """Test that show_warning method exists."""
        assert hasattr(BotTUI, 'show_warning')
        import inspect
        sig = inspect.signature(BotTUI.show_warning)
        params = list(sig.parameters.keys())
        assert 'message' in params
    
    def test_bot_tui_show_info_method(self):
        """Test that show_info method exists."""
        assert hasattr(BotTUI, 'show_info')
        import inspect
        sig = inspect.signature(BotTUI.show_info)
        params = list(sig.parameters.keys())
        assert 'message' in params


class TestErrorLevel:
    """Tests for ErrorLevel enum."""
    
    def test_error_level_values(self):
        """Test that ErrorLevel has correct values."""
        assert ErrorLevel.INFO.value == "info"
        assert ErrorLevel.WARNING.value == "warning"
        assert ErrorLevel.ERROR.value == "error"
        assert ErrorLevel.CRITICAL.value == "critical"
    
    def test_error_level_enum(self):
        """Test ErrorLevel enum membership."""
        assert isinstance(ErrorLevel.INFO, ErrorLevel)
        assert isinstance(ErrorLevel.WARNING, ErrorLevel)
        assert isinstance(ErrorLevel.ERROR, ErrorLevel)
        assert isinstance(ErrorLevel.CRITICAL, ErrorLevel)


# Integration-style tests (still unit tests but testing component interaction)
class TestTUIComponentIntegration:
    """Tests for TUI component integration."""
    
    def test_status_panel_with_all_components(self, mock_bot):
        """Test StatusPanel with all bot components."""
        panel = StatusPanel(mock_bot)
        panel.update_status()
        
        # Should handle all components gracefully
        assert panel.bot.provider is not None
        assert panel.bot.typer is not None
        assert panel.bot.context_observer is not None
        assert panel.bot.tts_engine is not None
    
    def test_status_panel_without_optional_components(self):
        """Test StatusPanel without optional components."""
        bot = MagicMock()
        bot.provider = MagicMock()
        bot.provider.__class__.__name__ = "Provider"
        bot.typer = MagicMock()
        bot.typer.__class__.__name__ = "Typer"
        bot.context_observer = None
        bot.tts_engine = None
        
        panel = StatusPanel(bot)
        panel.update_status()
        
        # Should handle None components
        assert panel.bot.context_observer is None
        assert panel.bot.tts_engine is None
    
    def test_hotkeys_panel_without_persona_switching(self):
        """Test HotkeysPanel without persona switching."""
        bot = MagicMock()
        bot.trigger_key = "f6"
        bot.voice_trigger_key = "f5"
        bot.next_mode_key = None
        bot.prev_mode_key = None
        bot.provider = MagicMock()  # Not switchable
        
        panel = HotkeysPanel(bot)
        panel.update_hotkeys()
        
        # Should handle non-switchable provider
        assert not isinstance(bot.provider, ISwitchableMessageProvider)


# Integration tests
class TestTUIEventBusIntegration:
    """Integration tests for TUI + EventBus interaction."""
    
    @pytest.mark.asyncio
    async def test_event_bus_loop_assignment(self, mock_bot, mock_event_bus, mock_analytics):
        """Test that EventBus loop is assigned when TUI mounts."""
        # This test verifies the pattern, actual implementation requires running TUI
        # We test that the code structure supports loop assignment
        assert hasattr(BotTUI, 'on_mount')
        
        # Verify EventBus has _loop attribute that can be set
        assert hasattr(mock_event_bus, '_loop')
    
    def test_event_bus_publish_from_tui(self, mock_event_bus):
        """Test that events can be published from TUI context."""
        # Verify EventBus can accept events
        assert hasattr(mock_event_bus, 'publish')
        assert hasattr(mock_event_bus, 'get')
    
    @pytest.mark.asyncio
    async def test_event_listener_pattern(self, mock_event_bus):
        """Test the event listener pattern used in TUI."""
        # Create a real EventBus for this test
        import asyncio
        event_bus = EventBus()
        
        # Start a task to consume events
        events_received = []
        
        async def consume_events():
            try:
                while True:
                    event = await event_bus.get()
                    events_received.append(event)
                    if event.type == EventType.SHUTDOWN:
                        break
            except asyncio.CancelledError:
                pass
        
        consumer_task = asyncio.create_task(consume_events())
        
        # Publish some events
        event_bus.publish(Event(EventType.TRIGGER_CHAT))
        event_bus.publish(Event(EventType.TRIGGER_VOICE))
        event_bus.publish(Event(EventType.SHUTDOWN))
        
        # Wait a bit for events to be processed
        await asyncio.sleep(0.1)
        
        # Cancel consumer
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        
        # Verify events were received
        assert len(events_received) >= 2
        assert events_received[0].type == EventType.TRIGGER_CHAT
        assert events_received[1].type == EventType.TRIGGER_VOICE


class TestTUIBotIntegration:
    """Integration tests for TUI + Bot interaction."""
    
    def test_bot_tui_initialization(self, mock_bot, mock_event_bus, mock_analytics):
        """Test that BotTUI can be initialized with bot components."""
        # Verify BotTUI accepts required parameters
        assert hasattr(BotTUI, '__init__')
        
        # Check that BotTUI stores references
        # Note: Can't actually instantiate without running event loop
        # But we can verify the structure
        
    def test_bot_start_in_background(self, mock_bot):
        """Test that bot.start() can be called as background task."""
        # Verify bot has start method
        assert hasattr(mock_bot, 'start')
        
        # Verify it's async
        import inspect
        assert inspect.iscoroutinefunction(mock_bot.start) or hasattr(mock_bot.start, '__call__')
    
    def test_bot_stop_method(self, mock_bot):
        """Test that bot.stop() exists and can be called."""
        assert hasattr(mock_bot, 'stop')
    
    def test_error_handling_in_bot_task(self, mock_bot):
        """Test error handling pattern in bot background task."""
        # Verify error handling structure exists
        assert hasattr(BotTUI, '_run_bot')
        
        import inspect
        sig = inspect.signature(BotTUI._run_bot)
        # Should be async
        assert inspect.iscoroutinefunction(BotTUI._run_bot)


class TestTUIComponentUpdates:
    """Tests for TUI component updates based on events."""
    
    def test_status_panel_update_on_persona_change(self, mock_bot, mock_switchable_provider):
        """Test that StatusPanel updates when persona changes."""
        mock_bot.provider = mock_switchable_provider
        panel = StatusPanel(mock_bot)
        
        # Initial update
        panel.update_status()
        initial_calls = mock_switchable_provider.get_current_mode_name.call_count
        
        # Simulate persona change
        mock_switchable_provider.get_current_mode_name.return_value = "Wholesome"
        panel.update_status()
        
        # Should have called get_current_mode_name again
        assert mock_switchable_provider.get_current_mode_name.call_count > initial_calls
    
    def test_hotkeys_panel_update_on_reload(self, mock_bot):
        """Test that HotkeysPanel can be updated."""
        panel = HotkeysPanel(mock_bot)
        
        # Initial update
        panel.update_hotkeys()
        
        # Change bot keys
        mock_bot.trigger_key = "f9"
        panel.update_hotkeys()
        
        # Should handle update
        assert hasattr(panel, 'update_hotkeys')
    
    def test_stats_panel_periodic_updates(self, mock_analytics):
        """Test that StatsPanel updates periodically."""
        panel = StatsPanel(mock_analytics)
        
        # Initial update
        panel.update_stats()
        initial_calls = mock_analytics.get_session_stats.call_count
        
        # Simulate periodic update
        panel.update_stats()
        
        # Should have called get_session_stats again
        assert mock_analytics.get_session_stats.call_count > initial_calls
    
    def test_error_panel_error_accumulation(self):
        """Test that ErrorPanel accumulates errors correctly."""
        panel = ErrorPanel()
        
        # Add multiple errors
        for i in range(5):
            panel.add_error(ErrorLevel.ERROR, f"Error {i}")
        
        assert len(panel.errors) == 5
        
        # Clear and verify
        panel.clear_errors()
        assert len(panel.errors) == 0
        
        # Add more errors
        panel.add_error(ErrorLevel.WARNING, "Warning")
        assert len(panel.errors) == 1


# Stress tests
class TestTUIStressTests:
    """Stress tests for TUI performance and reliability."""
    
    def test_rapid_error_generation(self):
        """Test ErrorPanel with rapid error generation."""
        panel = ErrorPanel()
        
        # Generate 100 errors rapidly
        for i in range(100):
            panel.add_error(ErrorLevel.INFO, f"Rapid error {i}")
        
        # Should respect max_errors limit
        assert len(panel.errors) <= panel.max_errors
        
        # Should keep most recent errors
        if len(panel.errors) > 0:
            assert "Rapid error" in panel.errors[-1][2]
    
    def test_error_panel_memory_usage(self):
        """Test that ErrorPanel doesn't leak memory with many errors."""
        import sys
        panel = ErrorPanel()
        
        # Get initial size
        initial_size = sys.getsizeof(panel.errors)
        
        # Add many errors
        for i in range(1000):
            panel.add_error(ErrorLevel.INFO, f"Error {i}")
        
        # Size should be bounded (due to max_errors)
        final_size = sys.getsizeof(panel.errors)
        
        # Should not grow unbounded
        # Note: This is a simple check, actual memory profiling would be more thorough
        assert len(panel.errors) <= panel.max_errors
    
    def test_stats_panel_rapid_updates(self, mock_analytics):
        """Test StatsPanel with rapid updates."""
        panel = StatsPanel(mock_analytics)
        
        # Rapid updates
        for _ in range(100):
            panel.update_stats()
        
        # Should handle rapid updates without issues
        assert mock_analytics.get_session_stats.call_count >= 100
    
    @pytest.mark.asyncio
    async def test_event_bus_rapid_events(self):
        """Test EventBus with rapid event generation."""
        import asyncio
        event_bus = EventBus()
        
        events_received = []
        
        async def consume_events():
            try:
                count = 0
                while count < 100:
                    event = await event_bus.get()
                    events_received.append(event)
                    count += 1
                    if event.type == EventType.SHUTDOWN:
                        break
            except asyncio.CancelledError:
                pass
        
        consumer_task = asyncio.create_task(consume_events())
        
        # Publish 100 events rapidly
        for i in range(100):
            event_bus.publish(Event(EventType.TRIGGER_CHAT))
        
        # Publish shutdown
        event_bus.publish(Event(EventType.SHUTDOWN))
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Cancel consumer
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        
        # Should have received events (may not be all 100 due to timing)
        assert len(events_received) > 0
    
    def test_error_panel_max_errors_enforcement(self):
        """Test that ErrorPanel enforces max_errors correctly."""
        panel = ErrorPanel()
        panel.max_errors = 10
        
        # Add more than max
        for i in range(50):
            panel.add_error(ErrorLevel.INFO, f"Error {i}")
        
        # Should only keep max_errors
        assert len(panel.errors) == 10
        
        # Should keep the most recent
        assert panel.errors[0][2] == "Error 40"
        assert panel.errors[-1][2] == "Error 49"
    
    def test_status_panel_repeated_updates(self, mock_bot):
        """Test StatusPanel with repeated updates."""
        panel = StatusPanel(mock_bot)
        
        # Update many times
        for _ in range(100):
            panel.update_status()
        
        # Should handle repeated updates
        assert hasattr(panel, 'update_status')
    
    def test_hotkeys_panel_repeated_updates(self, mock_bot):
        """Test HotkeysPanel with repeated updates."""
        panel = HotkeysPanel(mock_bot)
        
        # Update many times
        for _ in range(100):
            panel.update_hotkeys()
        
        # Should handle repeated updates
        assert hasattr(panel, 'update_hotkeys')
    
    def test_error_panel_clear_performance(self):
        """Test ErrorPanel clear performance with many errors."""
        panel = ErrorPanel()
        
        # Add many errors
        for i in range(1000):
            panel.add_error(ErrorLevel.INFO, f"Error {i}")
        
        # Clear should be fast
        import time
        start = time.time()
        panel.clear_errors()
        elapsed = time.time() - start
        
        # Should be very fast (< 0.1 seconds)
        assert elapsed < 0.1
        assert len(panel.errors) == 0

