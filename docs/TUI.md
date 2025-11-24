# TUI (Text User Interface) Documentation

## Overview

The R6 Nice Talker bot includes an opt-in Terminal User Interface (TUI) built with [Textual](https://textual.textualize.io/). The TUI provides a real-time, interactive terminal interface for monitoring bot status, events, and statistics without needing to check log files.

## Current Status

**Status**: ✅ **Functional (Opt-in)**

The TUI is fully functional but currently requires the `--tui` flag to enable. It provides real-time monitoring of bot operations, but console logging remains the default behavior.

## Features

### Real-Time Status Display
- **Provider Information**: Shows the current message provider (e.g., ChatGPTProvider)
- **Typer Information**: Displays the chat typer implementation in use
- **TTS Engine**: Shows the active Text-to-Speech engine (if configured)
- **Context Observer**: Displays the vision/context system in use (if configured)
- **Current Persona**: Shows the active persona when using switchable providers

### Hotkey Reference
- Displays all configured hotkey bindings
- Updates automatically when prompts are reloaded
- Shows trigger keys for chat and voice modes
- Displays persona switching keys (if available)

### Session Statistics
- **API Calls**: Count of API requests made
- **TTS Generations**: Number of voice messages generated
- **Total Tokens**: Cumulative token usage
- **Total Cost**: Calculated cost in USD
- **Average Latency**: Mean response time for API calls
- Updates every 5 seconds automatically

### Event Log
- Real-time scrollable log of all bot events
- Timestamped entries for each event
- Color-coded event types
- Shows TRIGGER_CHAT, TRIGGER_VOICE, NEXT_PERSONA, PREV_PERSONA, and other events

## Usage

### Enabling TUI Mode

Run the bot with the `--tui` flag:

```bash
python main.py --tui
```

You can combine it with other flags:

```bash
# TUI with verbose logging
python main.py --tui --verbose

# TUI with dry-run mode (no actual API calls)
python main.py --tui --dry-run
```

### TUI Controls

- **`q`**: Quit the TUI and stop the bot
- **`Ctrl+C`**: Quit the TUI and stop the bot
- **Mouse**: Click and scroll to interact with panels
- **Arrow Keys**: Navigate between panels (if focusable)

### Exiting TUI Mode

Press `q` or `Ctrl+C` to exit. The bot will:
1. Cancel all background tasks
2. Unhook keyboard listeners
3. End the analytics session
4. Display final session statistics in the console

## Architecture

### Component Structure

```
BotTUI (App)
├── StatusPanel
│   └── Displays bot component information
├── HotkeysPanel
│   └── Shows key bindings
├── StatsPanel
│   └── Session statistics (auto-updates)
└── EventLog
    └── Real-time event stream
```

### Event Integration

The TUI subscribes to the `EventBus` for real-time updates:

- **TRIGGER_CHAT**: Logs when chat messages are generated
- **TRIGGER_VOICE**: Logs when voice messages are generated
- **NEXT_PERSONA**: Updates status panel with new persona
- **PREV_PERSONA**: Updates status panel with new persona
- **PROMPTS_RELOADED**: Refreshes status and hotkeys panels
- **SHUTDOWN**: Gracefully exits the TUI

### Async Task Management

The TUI runs the bot as a background async task within Textual's event loop:

1. **Bot Task**: Runs `bot.start()` in the background
2. **Event Listener Task**: Consumes events from EventBus
3. **Stats Updater**: Updates statistics panel every 5 seconds
4. **Cleanup**: Properly cancels tasks on exit

## Error Handling

### Fallback Behavior

If TUI initialization fails, the bot automatically falls back to console mode:

```python
try:
    from src.tui import BotTUI
    tui_app = BotTUI(...)
    tui_app.run()
except ImportError:
    logger.warning("TUI module not available. Falling back to console mode.")
    # Continue with normal console logging
except Exception as e:
    logger.warning(f"TUI initialization failed: {e}. Falling back to console mode.")
    # Continue with normal console logging
```

### Common Issues

**Issue**: `textual` package not installed
- **Solution**: `pip install textual`
- **Fallback**: Bot continues in console mode

**Issue**: Terminal doesn't support TUI
- **Solution**: Use a modern terminal (Windows Terminal, PowerShell, or modern terminal emulator)
- **Fallback**: Bot continues in console mode

**Issue**: Event loop conflicts
- **Solution**: TUI mode uses Textual's event loop; console mode uses asyncio.run()
- **Note**: Both modes are properly isolated

## Implementation Details

### File Structure

```
src/
├── tui.py          # TUI implementation (BotTUI class)
└── ...

main.py             # Entry point with --tui flag support
requirements.txt    # Includes 'textual' dependency
```

### Key Classes

#### `BotTUI`
Main TUI application class extending `textual.app.App`.

**Key Methods**:
- `on_mount()`: Initializes bot and event listener tasks
- `_run_bot()`: Background task running the bot
- `_listen_events()`: Consumes EventBus events and updates UI
- `on_unmount()`: Cleanup on exit

#### `StatusPanel`
Displays bot component information.

#### `HotkeysPanel`
Shows configured hotkey bindings.

#### `StatsPanel`
Displays session statistics with auto-refresh.

### Event Loop Management

The TUI handles event loop management carefully:

1. **TUI Mode**: Uses Textual's synchronous `run()` method, which manages its own event loop
2. **Console Mode**: Uses `asyncio.run()` for async execution
3. **EventBus**: Updates loop reference when TUI starts to ensure keyboard callbacks work

## Future Work

To make TUI the default interface, the following work is needed:

### 1. Enhanced Error Recovery ⚠️ **HIGH PRIORITY**

**Current State**: TUI failures fall back to console mode, but error messages may be missed.

**Needed**:
- Better error display within TUI itself
- Error panel or notification system
- Graceful degradation (show errors in TUI instead of falling back)

**Example**:
```python
# Add error panel to TUI
class ErrorPanel(Static):
    """Display errors without exiting TUI"""
    ...
```

### 2. Interactive Controls 🔧 **MEDIUM PRIORITY**

**Current State**: TUI is read-only (monitoring only).

**Needed**:
- Interactive persona switching from TUI
- Manual trigger buttons for chat/voice
- Configuration editing interface
- Hotkey rebinding interface

**Example**:
```python
# Add interactive buttons
with Horizontal():
    yield Button("Trigger Chat", id="btn-chat")
    yield Button("Trigger Voice", id="btn-voice")
    yield Button("Next Persona", id="btn-next")
```

### 3. Enhanced Statistics 📊 **MEDIUM PRIORITY**

**Current State**: Basic session statistics displayed.

**Needed**:
- Historical statistics (last hour, day, week)
- Cost trends and projections
- Token usage charts
- Latency distribution graphs
- Export functionality (CSV, JSON)

**Example**:
```python
# Add charts using textual's built-in widgets
yield Sparkline(data=recent_costs, id="cost-trend")
```

### 4. Configuration Management ⚙️ **LOW PRIORITY**

**Current State**: Configuration must be edited in `.env` file.

**Needed**:
- TUI-based configuration editor
- Real-time configuration updates
- Validation and error checking
- Configuration presets/profiles

### 5. Log Viewer Integration 📝 **LOW PRIORITY**

**Current State**: Event log shows real-time events only.

**Needed**:
- File log viewer (read from `bot.log`)
- Log filtering and search
- Log level filtering (INFO, DEBUG, ERROR)
- Export log functionality

### 6. Performance Optimizations 🚀 **LOW PRIORITY**

**Current State**: Works well but could be optimized.

**Needed**:
- Lazy loading of heavy components (OCR initialization)
- Reduced refresh frequency for stats (configurable)
- Virtual scrolling for long event logs
- Memory usage monitoring

### 7. Testing & Reliability 🧪 **HIGH PRIORITY**

**Current State**: Basic functionality tested.

**Needed**:
- Unit tests for TUI components
- Integration tests for TUI + bot interaction
- Stress testing (rapid events, long sessions)
- Cross-platform testing (Windows, Linux, macOS)
- Terminal compatibility testing

### 8. Documentation & UX 📚 **MEDIUM PRIORITY**

**Current State**: Basic documentation exists.

**Needed**:
- In-TUI help system (press `?` for help)
- Keyboard shortcut reference overlay
- Tooltips for all UI elements
- User guide/tutorial mode
- Accessibility improvements (screen reader support)

### 9. Making TUI the Default 🎯 **FUTURE GOAL**

**Current State**: TUI is opt-in via `--tui` flag.

**Requirements Before Default**:
1. ✅ Error handling and fallback
2. ⚠️ Enhanced error recovery (see #1)
3. ⚠️ Interactive controls (see #2)
4. ⚠️ Comprehensive testing (see #7)
5. ⚠️ User documentation (see #8)

**Migration Path**:
```python
# Future: TUI as default, --console flag for console mode
if args.console:  # New flag
    await app.start()  # Console mode
else:
    run_tui_mode(...)  # TUI mode (default)
```

**Considerations**:
- Some users may prefer console mode (automation, scripts)
- TUI requires terminal support (may not work in all environments)
- Need to ensure TUI works reliably before making default
- Should maintain backward compatibility

## Contributing

### Adding New TUI Features

1. **Create Widget**: Add new panel/widget class in `src/tui.py`
2. **Integrate**: Add to `BotTUI.compose()` method
3. **Connect Events**: Subscribe to relevant EventBus events
4. **Test**: Test with `--tui --dry-run` flag
5. **Document**: Update this file with new features

### Example: Adding a New Panel

```python
class MyNewPanel(Static):
    """Description of what this panel does."""
    
    def compose(self) -> ComposeResult:
        yield Static("My Panel", classes="panel-title")
        yield Static(id="my-content")
    
    def on_mount(self) -> None:
        self.update_content()
    
    def update_content(self) -> None:
        content = "My panel content"
        self.query_one("#my-content").update(content)

# In BotTUI.compose():
yield MyNewPanel(id="my-panel")
```

## Troubleshooting

### TUI Won't Start

1. **Check Textual Installation**:
   ```bash
   python -c "import textual; print(textual.__version__)"
   ```

2. **Check Terminal Support**:
   - Use Windows Terminal or modern terminal emulator
   - Ensure terminal supports ANSI colors

3. **Check Logs**:
   - Look for error messages in console output
   - Check `bot.log` for detailed errors

### TUI Starts But Bot Doesn't Work

1. **Check Event Loop**:
   - Ensure EventBus is properly initialized
   - Check that keyboard listeners are registered

2. **Check Permissions**:
   - Bot still needs Administrator privileges
   - TUI doesn't change permission requirements

### Performance Issues

1. **Reduce Stats Refresh Rate**:
   - Edit `StatsPanel.set_interval()` in `src/tui.py`
   - Default is 5 seconds

2. **Limit Event Log Size**:
   - Currently unlimited; consider adding max lines
   - Can be implemented in `_listen_events()`

## References

- [Textual Documentation](https://textual.textualize.io/)
- [Textual GitHub](https://github.com/Textualize/textual)
- [Event Bus Architecture](./architecture/event_bus.md)
- [Development Guide](./DEVELOPMENT.md)

