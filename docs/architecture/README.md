# Architecture Documentation

This folder contains technical documentation about the R6 Nice Talker architecture.

## Documents

| Document | Description |
|----------|-------------|
| [component-diagram.md](./component-diagram.md) | High-level component dependencies and layers |
| [event-bus.md](./event-bus.md) | Thread-safe async event communication |
| [message-flow.md](./message-flow.md) | Text message generation sequence |
| [voice-flow.md](./voice-flow.md) | Voice generation and audio playback sequence |
| [vision-pipeline.md](./vision-pipeline.md) | OCR/screen capture for game context |

## Design Principles

### Interface-Based Architecture
All major components implement interfaces defined in `src/interfaces.py`:
- `IMessageProvider` - Message generation
- `IChatTyper` - Game input simulation
- `ITextToSpeech` - Voice synthesis
- `IAudioPlayer` - Audio output
- `IContextObserver` - Game state detection

### Factory Pattern
`src/factory.py` creates concrete implementations based on `.env` configuration, enabling easy swapping of providers without code changes.

### Event-Driven Communication
The EventBus (`src/events.py`) bridges thread-based keyboard callbacks with the async main loop, ensuring thread-safe operation.

### Singleton Services
Config, Cache, and Analytics use singleton patterns for global access and consistent state.

## Quick Reference

```
User Input (Hotkey)
    ↓
Keyboard Thread → EventBus.publish()
    ↓
Main Async Loop → Bot Controller
    ↓
┌───────────────────────────────────────┐
│  Provider → Cache → API → Analytics   │
└───────────────────────────────────────┘
    ↓
Typer/TTS → Game
```
