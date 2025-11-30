# TUI (Terminal User Interface)

The R6 Nice Talker bot includes an optional Terminal User Interface built with [Textual](https://textual.textualize.io/). The TUI provides real-time monitoring, configuration management, and analytics visualization.

## Quick Start

```bash
# Enable TUI mode
python main.py --tui

# TUI with dry-run (no API calls)
python main.py --tui --dry-run

# TUI with verbose logging
python main.py --tui --verbose
```

**Controls:**
- `q` or `Ctrl+C` - Quit
- `F1` or `?` - Open help screen
- Mouse/Arrow keys - Navigate panels

## Features

### Status Panel
- Current message provider (ChatGPT, Fixed, Random)
- Chat typer implementation in use
- Active TTS engine
- Context observer (OCR engine)
- Current persona name

### Hotkey Reference
- All configured hotkey bindings
- Updates when prompts are reloaded
- Shows trigger keys for chat/voice modes

### Session Statistics
Real-time metrics updated every 5 seconds:
- API call count
- TTS generations
- Total tokens used
- Cumulative cost (USD)
- Average latency
- **Sparkline visualizations** for cost and latency trends

### Event Log
- Real-time scrollable log of bot events
- Timestamped entries
- Color-coded event types (TRIGGER_CHAT, TRIGGER_VOICE, etc.)

### Tabbed Interface
Three main tabs for organized access:
1. **Events** - Real-time event log
2. **Logs** - Interactive `bot.log` viewer with filtering
3. **Config** - In-TUI `.env` editor

## Log Viewer

View and filter the bot log file without leaving the TUI:

- **Level filter**: ALL, DEBUG, INFO, WARNING, ERROR
- **Text search**: Case-insensitive substring matching
- **Refresh**: Reload from file
- **Clear**: Reset display
- Performance-optimized (1000 line limit)

## Configuration Editor

Edit `.env` directly in the TUI:

1. Switch to "Config" tab
2. Edit configuration in text area
3. Click "Save" (auto-creates `.env.backup`)
4. Restart application for changes to take effect

## Statistics Export

Export session data for external analysis:

1. Click "Export" in Statistics panel
2. Select time range (Session, 1h, 24h, 7d)
3. Choose format (CSV or JSON)
4. File saved as `r6_stats_{range}_{timestamp}.{ext}`

## Architecture

```
BotTUI (App)
├── StatusPanel      - Bot component information
├── HotkeysPanel     - Key bindings
├── StatsPanel       - Statistics with sparklines
└── TabbedContent
    ├── EventLog     - Real-time event stream
    ├── LogViewerPanel - Log file with filtering
    └── ConfigPanel  - .env editor
```

### Event Integration

The TUI subscribes to EventBus for real-time updates:
- `TRIGGER_CHAT` / `TRIGGER_VOICE` - Log message generation
- `NEXT_PERSONA` / `PREV_PERSONA` - Update status panel
- `PROMPTS_RELOADED` - Refresh panels
- `SHUTDOWN` - Graceful exit

### Async Task Management

1. **Bot Task**: Runs `bot.start()` in background
2. **Event Listener**: Consumes EventBus events
3. **Stats Updater**: Refreshes statistics every 5 seconds
4. **Cleanup**: Properly cancels tasks on exit

## Error Handling

If TUI initialization fails, the bot automatically falls back to console mode:

```python
try:
    tui_app = BotTUI(...)
    tui_app.run()
except ImportError:
    logger.warning("TUI module not available")
    # Continue with console logging
```

## Troubleshooting

### TUI Won't Start
1. Check Textual: `python -c "import textual; print(textual.__version__)"`
2. Use modern terminal (Windows Terminal, PowerShell)
3. Check `bot.log` for errors

### Sparklines Don't Appear
- Requires recent Textual version
- Run: `pip install --upgrade textual`
- Statistics work without visualizations

### Performance Issues
- Reduce stats refresh rate in `src/tui.py` (default 5s)
- Log viewer limited to 1000 lines

### Bot Not Responding in TUI
- Administrator privileges still required
- Check EventBus initialization
- Verify keyboard listeners registered

## Adding New TUI Features

```python
# 1. Create widget in src/tui.py
class MyPanel(Static):
    def compose(self) -> ComposeResult:
        yield Static("My Panel", classes="panel-title")
        yield Static(id="my-content")

    def update_content(self) -> None:
        self.query_one("#my-content").update("content")

# 2. Add to BotTUI.compose()
yield MyPanel(id="my-panel")

# 3. Connect to events if needed
# 4. Test with: python main.py --tui --dry-run
```

## References

- [Textual Documentation](https://textual.textualize.io/)
- [Event Bus Architecture](./architecture/event-bus.md)
- [Development Guide](./development.md)
