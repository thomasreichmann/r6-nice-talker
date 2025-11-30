# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

R6 Nice Talker is an AI-powered chat bot for Rainbow Six Siege that generates contextual, persona-based messages and injects them into the game chat. It uses OpenAI's GPT models to create dynamic messages with multiple personalities while handling real-time game interaction via simulated keyboard input.

## Development Commands

```bash
# Run the application
python main.py                    # Console mode (default)
python main.py --tui              # Terminal UI mode
python main.py --dry-run          # Mock API calls, no typing
python main.py --verbose          # Debug logging

# Run tests
pytest tests/                     # All tests
pytest tests/test_bot.py          # Single test file
pytest tests/ -v                  # Verbose output

# Standalone component testing
python tools/test_messages.py --persona Toxic --dry-run
python tools/test_tts.py --text "Hello" --provider pyttsx3
python tools/test_vision.py --roi killfeed --engine easyocr
python tools/test_typer.py --text "test" --dry-run

# GUI launcher (analytics, config editor, prompt editor)
python gui_launcher.py

# Health check (validate setup)
python -m src.health_check
```

## Architecture

### Core Pattern: Interface-Based Dependency Injection

All major components implement interfaces from `src/interfaces.py`:
- `IMessageProvider` - Message generation (ChatGPT, Random, Fixed)
- `IChatTyper` - Sends messages to game (R6SiegeTyper, DebugTyper)
- `ITextToSpeech` - TTS conversion (ElevenLabs, pyttsx3)
- `IAudioPlayer` - Audio playback (SoundDevicePlayer)
- `IContextObserver` - Game state detection via OCR

`src/factory.py` creates concrete implementations based on `.env` configuration.

### Event-Driven Flow

```
Hotkey (F6) → Keyboard Thread → EventBus.publish() → Main Async Loop → Bot._process_trigger_chat()
                                                                            ├→ Get game context (OCR)
                                                                            ├→ Generate message (API)
                                                                            ├→ Track analytics
                                                                            └→ Type to game
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `src/bot.py` | Main controller, hotkey binding, orchestration |
| `src/providers.py` | Message generation strategies |
| `src/typers.py` | Keyboard input simulation for game chat |
| `src/voice.py` | TTS engines and audio playback |
| `src/vision.py` | OCR for game context detection |
| `src/events.py` | Thread-safe async event bus |
| `src/analytics.py` | Usage tracking and cost calculation |
| `src/factory.py` | Factory pattern for DI based on config |
| `src/tui.py` | Textual-based terminal UI |

### Entry Points

- `main.py` - CLI entry (console or TUI mode)
- `gui_launcher.py` - GUI unified launcher
- `debug_rois.py` - ROI editor tool for OCR regions

## Configuration

All settings in `.env` (see `env.example`):
- `MESSAGE_PROVIDER`: `chatgpt`, `random`, or `fixed`
- `TTS_PROVIDER`: `pyttsx3` or `elevenlabs`
- `VISION_ENGINE`: `easyocr` or `tesseract`
- `DRY_RUN`: Mock API and typing for development
- `DEV_CACHE_ENABLED`: Cache API responses to reduce costs

Personas defined in `prompts.json` (8 built-in: Preacher, Toxic, Wholesome, FalleN, etc.)

## Important Patterns

### Async/Threading
- Main loop is fully async
- Keyboard callbacks run in separate threads
- EventBus uses `call_soon_threadsafe` for thread safety
- Blocking operations use `await loop.run_in_executor(None, func)`

### Game Input
- Games read DirectInput, not OS signals
- Keys must be "held" for ~50ms to register
- Uses `pydirectinput` with safety delays

### Post-Processing Pipeline
Messages go through: `remove_emojis()` → truncate to max length → type to game

## Adding New Components

**New Provider**: Implement `IMessageProvider` in `src/providers.py`, register in `src/factory.py`

**New TTS Engine**: Implement `ITextToSpeech` in `src/voice.py`, register in factory

**New Event**: Add to `EventType` enum in `src/events.py`, handle in `src/bot.py`

## Documentation

```
docs/
├── development.md          # Testing tools, debugging, cost management
├── tui.md                  # Terminal UI features and usage
├── learnings.md            # Design patterns and lessons learned
├── roadmap.md              # Future features and enhancements
└── architecture/
    ├── README.md           # Architecture overview
    ├── component-diagram.md
    ├── event-bus.md
    ├── message-flow.md
    ├── voice-flow.md
    └── vision-pipeline.md
```

Also see: `CONTRIBUTING.md` for architecture patterns and how to add features.
