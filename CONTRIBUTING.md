# Contributing to R6 Nice Talker

Thank you for your interest in contributing! This guide will help you understand the project architecture and how to contribute effectively.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Component Responsibilities](#component-responsibilities)
- [Development Setup](#development-setup)
- [Testing Guidelines](#testing-guidelines)
- [How to Add New Features](#how-to-add-new-features)
- [PR Process](#pr-process)

## Architecture Overview

The project uses a **factory pattern** with **interface-based dependency injection** and an **event-driven architecture** for async communication.

### High-Level Flow

```
User Input (Hotkey) → Event Bus → Bot Controller → Provider/TTS/Typer → Game
```

See [docs/architecture/](docs/architecture/) for detailed Mermaid diagrams.

### Key Architectural Patterns

1. **Interfaces**: All components implement interfaces (see `src/interfaces.py`)
   - `IMessageProvider`: Generates messages
   - `IChatTyper`: Types messages into game
   - `ITextToSpeech`: Converts text to speech
   - `IContextObserver`: Provides game context (Vision, Audio, etc.)

2. **Factory**: `src/factory.py` creates concrete implementations based on config

3. **Event Bus**: `src/events.py` handles async event propagation
   - Keyboard callbacks (threads) → Event Bus → Main loop (async)
   - Decouples hotkey handling from business logic

4. **Config Management**: `src/config.py` loads from `.env` file

## Component Responsibilities

### Core Modules

- **`src/bot.py`**: Main controller, binds hotkeys, orchestrates message generation
- **`src/providers.py`**: Message generation implementations (ChatGPT, Fixed, Random)
- **`src/typers.py`**: Chat typing implementations (R6Siege, Debug)
- **`src/voice.py`**: TTS engines (ElevenLabs, pyttsx3) and audio playback
- **`src/vision.py`**: OCR/context detection (EasyOCR, Tesseract)
- **`src/events.py`**: Event bus for async communication
- **`src/cache.py`**: Development cache for API responses
- **`src/analytics.py`**: Usage tracking and cost calculation

### Supporting Modules

- **`src/config.py`**: Configuration management
- **`src/constants.py`**: System prompts and templates
- **`src/context.py`**: Random context generation
- **`src/sounds.py`**: Sound feedback
- **`src/utils.py`**: Utility functions (latency measurement, emoji removal)

### Tools

- **`tools/test_tts.py`**: Test TTS engines standalone
- **`tools/test_messages.py`**: Test message generation standalone
- **`tools/test_vision.py`**: Test OCR/vision standalone
- **`tools/test_typer.py`**: Test typing behavior standalone

### GUI

- **`gui/components.py`**: Reusable DearPyGui widgets
- **`gui/analytics_dashboard.py`**: Cost and usage visualization
- **`gui/config_editor.py`**: Visual `.env` editor
- **`gui/prompt_editor.py`**: Persona management with live preview
- **`gui_launcher.py`**: Main GUI entry point

## Development Setup

### Prerequisites

- Python 3.10+
- Tesseract OCR (optional, for vision)
- Virtual Audio Cable (optional, for voice)

### Quick Setup

```bash
# Clone repository
git clone https://github.com/yourusername/r6-nice-talker.git
cd r6-nice-talker

# Run automated setup
python setup.py

# Or manual setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env
# Edit .env with your API keys
```

### Health Check

```bash
python -m src.health_check
```

This validates:
- Python version
- Package installation
- `.env` configuration
- Tesseract installation
- Audio devices
- API keys

## Testing Guidelines

### Before Running the Bot

**Always test components in isolation first** using the standalone tools:

```bash
# Test TTS without running bot
python tools/test_tts.py --text "Hello" --provider pyttsx3

# Test message generation (with dry-run to avoid API costs)
python tools/test_messages.py --persona Toxic --dry-run

# Test vision/OCR
python tools/test_vision.py --engine easyocr --roi killfeed

# Test typing behavior
python tools/test_typer.py --text "test" --dry-run
```

### Development Modes

#### Dry-Run Mode
Test without actual API calls or typing:
```bash
python main.py --dry-run
```

#### Verbose Mode
Enable DEBUG logging with JSON format:
```bash
python main.py --verbose
```

#### Cache Mode
Enable caching to avoid redundant API calls during development:
```env
# In .env
DEV_CACHE_ENABLED=true
DEV_CACHE_TTL=86400  # 24 hours
```

#### Hot-Reload
Auto-reload prompts when `prompts.json` changes:
```env
PROMPTS_HOT_RELOAD=true
```

### Unit Tests

Run existing tests:
```bash
pytest tests/
```

When adding features, write tests in `tests/`:
- Test edge cases
- Mock external dependencies (API calls, file I/O)
- Use fixtures from `tests/conftest.py`

## How to Add New Features

### Adding a New Message Provider

1. **Implement the interface** in `src/providers.py`:

```python
class MyCustomProvider(IMessageProvider):
    async def get_message(self, mode: str = "text", context_override: str = None) -> str:
        # Your implementation
        return "Generated message"
```

2. **Register in factory** (`src/factory.py`):

```python
def get_message_provider(event_bus=None):
    if Config.MESSAGE_PROVIDER_TYPE == 'mycustom':
        return MyCustomProvider()
    # ...existing code
```

3. **Add config** in `src/config.py`:

```python
MESSAGE_PROVIDER_TYPE = os.getenv("MESSAGE_PROVIDER", "mycustom").lower()
```

4. **Update `.env.example`** with new option

5. **Test standalone**:
```bash
python -c "from src.providers import MyCustomProvider; import asyncio; asyncio.run(MyCustomProvider().get_message())"
```

### Adding a New TTS Engine

1. **Implement interface** in `src/voice.py`:

```python
class MyTTS(ITextToSpeech):
    async def synthesize(self, text: str) -> str:
        # Return path to audio file
        return "/path/to/audio.wav"
```

2. **Add analytics tracking**:

```python
from src.analytics import get_analytics
analytics = get_analytics()
analytics.track_tts(provider="mytts", char_count=len(text), latency_ms=elapsed)
```

3. **Register in factory** (`src/factory.py`)

4. **Test with tool**:
```bash
# Extend tools/test_tts.py to support new provider
```

### Adding a New Context Observer

1. **Implement interface** in appropriate module:

```python
class AudioListener(IContextObserver):
    def get_context(self) -> str:
        # Analyze game audio, return context string
        return "Detected footsteps nearby"
```

2. **Register in factory** (`src/factory.py`)

3. **Context is automatically passed** to message provider

### Adding a New Event Type

1. **Add to enum** in `src/events.py`:

```python
class EventType(Enum):
    # ...existing
    MY_NEW_EVENT = auto()
```

2. **Publish event** where needed:

```python
event_bus.publish(Event(EventType.MY_NEW_EVENT, data={"key": "value"}))
```

3. **Handle event** in `src/bot.py`:

```python
elif event.type == EventType.MY_NEW_EVENT:
    self._handle_my_event(event.data)
```

## PR Process

### Before Submitting

1. **Test your changes**:
   - Run standalone tools for affected components
   - Run `pytest tests/`
   - Test with `--dry-run` flag
   - Run `python -m src.health_check`

2. **Check code quality**:
   - Follow existing code style (PEP 8)
   - Add docstrings to new functions/classes
   - Update type hints

3. **Update documentation**:
   - Update relevant docs if behavior changes
   - Add examples to docstrings
   - Update `.env.example` if adding config

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested with standalone tools
- [ ] Added/updated unit tests
- [ ] Tested with dry-run mode
- [ ] Health check passes

## Screenshots (if applicable)
For GUI changes

## Checklist
- [ ] Code follows project style
- [ ] Added docstrings
- [ ] Updated documentation
- [ ] No new linter errors
```

### Review Process

1. Submit PR with clear description
2. CI will run tests automatically
3. Maintainer will review within 2-3 days
4. Address feedback if needed
5. PR merged once approved

## Code Style Guidelines

- **Imports**: Group by standard library, third-party, local
- **Type hints**: Use for function signatures
- **Docstrings**: Google style for all public functions
- **Logging**: Use appropriate levels (DEBUG, INFO, WARNING, ERROR)
- **Error handling**: Catch specific exceptions, log errors
- **Async**: Use `async/await` for I/O operations

## Questions?

- Open an issue for questions
- Check existing issues/PRs first
- Be respectful and constructive

Thank you for contributing!

