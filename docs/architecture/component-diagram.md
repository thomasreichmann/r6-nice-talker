## Factory and Implementations

- **`src/factory.py`**
  - Acts as a simple dependency injection container.
  - Based on configuration, it chooses concrete implementations for:
    - Providers (`src/providers.py`).
    - Typers (`src/typers.py`).
    - Voice / TTS engines (`src/voice.py`).
    - Vision / OCR observers (`src/vision.py`).

- **Providers (`src/providers.py`)**
  - Implement the `IMessageProvider` interface.
  - Depend on:
    - `src/config.py` for API keys, model configuration, and feature flags.
    - `src/cache.py` for response caching.
    - `src/analytics.py` for tracking token usage and costs.
    - `src/constants.py` for reusable prompt fragments and defaults.

- **Typers (`src/typers.py`)**
  - Implement the `IChatTyper` interface.
  - Use `src/config.py` to respect settings like typing delays and key bindings.

- **Voice / TTS (`src/voice.py`)**
  - Implement the `ITextToSpeech` interface.
  - Depend on `src/config.py` for provider selection and audio device names.
  - Report usage and latency to `src/analytics.py`.

- **Vision / OCR (`src/vision.py`)**
  - Implement the `IContextObserver` interface.
  - Use `src/config.py` to locate ROI definitions and engine choices.
  - Send performance metrics to `src/analytics.py`.

## Shared Infrastructure

- **`src/interfaces.py`**
  - Defines all the core contracts (`IMessageProvider`, `IChatTyper`, `ITextToSpeech`, `IContextObserver`, etc.).
  - Allows components to be swapped or mocked in tests without changing the bot logic.

- **`src/config.py`**
  - Central configuration layer, typically reading from the `.env` file and environment variables.
  - Provides typed accessors for settings used throughout providers, typers, voice, and vision.

- **`src/analytics.py`**
  - Records API usage (tokens, cost, latency) and TTS metrics.
  - Used by providers, TTS engines, and vision to log operational data.

- **`src/cache.py`**
  - Holds short‑lived cached responses to reduce repeated API calls during development.

- **`.env` file**
  - Source of secrets and environment-specific configuration (API keys, device names, feature toggles).

