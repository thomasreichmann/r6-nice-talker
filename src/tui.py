"""
TUI (Text User Interface) module using Textual framework.
Provides a terminal-based UI for monitoring bot status and events.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Log, DataTable
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual import events
from src.events import EventBus, Event, EventType
from src.interfaces import ISwitchableMessageProvider

logger = logging.getLogger(__name__)


class StatusPanel(Static):
    """Panel displaying bot status information."""
    
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
    
    def compose(self) -> ComposeResult:
        yield Static("Status", classes="panel-title")
        yield Static(id="status-content")
    
    def on_mount(self) -> None:
        self.update_status()
    
    def update_status(self) -> None:
        """Update status display with current bot information."""
        provider_name = self.bot.provider.__class__.__name__
        typer_name = self.bot.typer.__class__.__name__
        
        status_lines = [
            f"[bold]Provider:[/bold] {provider_name}",
            f"[bold]Typer:[/bold] {typer_name}",
        ]
        
        if self.bot.context_observer:
            observer_name = self.bot.context_observer.__class__.__name__
            status_lines.append(f"[bold]Context Observer:[/bold] {observer_name}")
        else:
            status_lines.append("[bold]Context Observer:[/bold] None")
        
        if self.bot.tts_engine:
            tts_name = self.bot.tts_engine.__class__.__name__
            status_lines.append(f"[bold]TTS Engine:[/bold] {tts_name}")
        else:
            status_lines.append("[bold]TTS Engine:[/bold] None")
        
        if isinstance(self.bot.provider, ISwitchableMessageProvider):
            persona_name = self.bot.provider.get_current_mode_name()
            status_lines.append(f"[bold]Current Persona:[/bold] {persona_name}")
        
        self.query_one("#status-content").update("\n".join(status_lines))


class HotkeysPanel(Static):
    """Panel displaying hotkey bindings."""
    
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
    
    def compose(self) -> ComposeResult:
        yield Static("Hotkeys", classes="panel-title")
        yield Static(id="hotkeys-content")
    
    def on_mount(self) -> None:
        self.update_hotkeys()
    
    def update_hotkeys(self) -> None:
        """Update hotkeys display."""
        hotkey_lines = [
            f"[bold]{self.bot.trigger_key}:[/bold] Generate & Type Message",
            f"[bold]{self.bot.voice_trigger_key}:[/bold] Generate & Speak Message",
        ]
        
        if isinstance(self.bot.provider, ISwitchableMessageProvider):
            if self.bot.next_mode_key:
                hotkey_lines.append(f"[bold]{self.bot.next_mode_key}:[/bold] Next Persona")
            if self.bot.prev_mode_key:
                hotkey_lines.append(f"[bold]{self.bot.prev_mode_key}:[/bold] Previous Persona")
        
        hotkey_lines.append("[bold]Ctrl+C:[/bold] Quit")
        
        self.query_one("#hotkeys-content").update("\n".join(hotkey_lines))


class StatsPanel(Static):
    """Panel displaying session statistics."""
    
    def __init__(self, analytics, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analytics = analytics
    
    def compose(self) -> ComposeResult:
        yield Static("Statistics", classes="panel-title")
        yield Static(id="stats-content")
    
    def on_mount(self) -> None:
        self.update_stats()
        self.set_interval(5.0, self.update_stats)  # Update every 5 seconds
    
    def update_stats(self) -> None:
        """Update statistics display."""
        stats = self.analytics.get_session_stats() if self.analytics else {}
        
        if not stats:
            self.query_one("#stats-content").update("[dim]No session data[/dim]")
            return
        
        stats_lines = [
            f"[bold]API Calls:[/bold] {stats.get('api_call_count', 0)}",
            f"[bold]TTS Generations:[/bold] {stats.get('tts_count', 0)}",
            f"[bold]Total Tokens:[/bold] {stats.get('total_tokens', 0)}",
            f"[bold]Total Cost:[/bold] ${stats.get('total_cost', 0):.6f}",
            f"[bold]Avg Latency:[/bold] {stats.get('avg_latency_ms', 0):.0f}ms",
        ]
        
        self.query_one("#stats-content").update("\n".join(stats_lines))


class BotTUI(App):
    """Main TUI application for the bot."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .panel-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    #status-panel, #hotkeys-panel, #stats-panel {
        height: auto;
        border: solid $primary;
        padding: 1;
        margin: 1;
    }
    
    #event-log {
        border: solid $primary;
        padding: 1;
        margin: 1;
    }
    
    Horizontal {
        height: auto;
    }
    
    Vertical {
        height: 1fr;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True),
    ]
    
    def __init__(self, bot, event_bus: EventBus, analytics=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.event_bus = event_bus
        self.analytics = analytics
        self._event_task: Optional[asyncio.Task] = None
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Vertical():
            with Horizontal():
                yield StatusPanel(self.bot, id="status-panel")
                yield HotkeysPanel(self.bot, id="hotkeys-panel")
                yield StatsPanel(self.analytics, id="stats-panel")
            
            yield Log(id="event-log", highlight=True)
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = "R6 Nice Talker - Bot Monitor"
        self.sub_title = "Press 'q' or Ctrl+C to quit"
        
        # Update EventBus to use Textual's event loop
        try:
            loop = asyncio.get_running_loop()
            self.event_bus._loop = loop
        except RuntimeError:
            pass
        
        # Start bot as background task
        self._bot_task = asyncio.create_task(self._run_bot())
        
        # Start event listener task
        self._event_task = asyncio.create_task(self._listen_events())
        
        # Log initial message
        self.query_one("#event-log").write(f"[{datetime.now().strftime('%H:%M:%S')}] Bot started")
    
    async def _run_bot(self) -> None:
        """Run the bot in the background."""
        try:
            await self.bot.start()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Bot error: {e}", exc_info=True)
            event_log = self.query_one("#event-log")
            event_log.write(f"[{datetime.now().strftime('%H:%M:%S')}] [red]Bot error: {e}[/red]")
    
    async def on_unmount(self) -> None:
        """Called when the app is unmounted."""
        # Cancel bot task
        if hasattr(self, '_bot_task') and self._bot_task:
            self._bot_task.cancel()
            try:
                await self._bot_task
            except asyncio.CancelledError:
                pass
        
        # Stop bot
        self.bot.stop()
        
        # Cancel event listener task
        if self._event_task:
            self._event_task.cancel()
            try:
                await self._event_task
            except asyncio.CancelledError:
                pass
    
    async def _listen_events(self) -> None:
        """Listen to EventBus events and update the UI."""
        event_log = self.query_one("#event-log")
        status_panel = self.query_one("#status-panel")
        hotkeys_panel = self.query_one("#hotkeys-panel")
        
        try:
            while True:
                event = await self.event_bus.get()
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                # Log event
                event_type_name = event.type.name.replace('_', ' ').title()
                event_log.write(f"[{timestamp}] {event_type_name}")
                
                # Update UI based on event type
                if event.type == EventType.NEXT_PERSONA or event.type == EventType.PREV_PERSONA:
                    # Update status panel to show new persona
                    await asyncio.sleep(0.1)  # Small delay to ensure provider updated
                    status_panel.update_status()
                
                elif event.type == EventType.PROMPTS_RELOADED:
                    status_panel.update_status()
                    hotkeys_panel.update_hotkeys()
                
                elif event.type == EventType.SHUTDOWN:
                    event_log.write(f"[{timestamp}] Shutting down...")
                    await asyncio.sleep(0.5)
                    # Cancel bot task
                    if hasattr(self, '_bot_task') and self._bot_task:
                        self._bot_task.cancel()
                    self.exit()
                    break
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in event listener: {e}", exc_info=True)
            event_log.write(f"[{datetime.now().strftime('%H:%M:%S')}] [red]Error: {e}[/red]")
    
    def action_quit(self) -> None:
        """Handle quit action."""
        self.exit()

