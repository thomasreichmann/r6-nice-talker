# Component Dependency Diagram

This diagram shows the high-level component relationships and dependencies in the R6 Nice Talker project.

```mermaid
graph TB
    Main[main.py] --> Factory[factory.py]
    Main --> Bot[bot.py]
    Main --> EventBus[events.py]
    Main --> Analytics[analytics.py]
    
    Bot --> Interfaces[interfaces.py]
    Bot --> EventBus
    Bot --> Provider[IMessageProvider]
    Bot --> Typer[IChatTyper]
    Bot --> TTS[ITextToSpeech]
    Bot --> Observer[IContextObserver]
    
    Factory --> Providers[providers.py]
    Factory --> Typers[typers.py]
    Factory --> Voice[voice.py]
    Factory --> Vision[vision.py]
    
    Providers -.implements.-> Provider
    Providers --> Config[config.py]
    Providers --> Cache[cache.py]
    Providers --> Analytics
    Providers --> Constants[constants.py]
    
    Typers -.implements.-> Typer
    Typers --> Config
    
    Voice -.implements.-> TTS
    Voice --> Config
    Voice --> Analytics
    
    Vision -.implements.-> Observer
    Vision --> Config
    Vision --> Analytics
    
    Config --> Env[.env file]
    
    style Interfaces fill:#e1f5ff
    style Provider fill:#e1f5ff
    style Typer fill:#e1f5ff
    style TTS fill:#e1f5ff
    style Observer fill:#e1f5ff
    style Main fill:#fff4e1
    style Bot fill:#fff4e1
```

## Component Layers

### Layer 1: Interfaces
- **`src/interfaces.py`**: Defines contracts for all pluggable components
- Enables dependency injection and testability

### Layer 2: Implementations
- **`src/providers.py`**: Message generation (ChatGPT, Fixed, Random)
- **`src/typers.py`**: Chat typing (R6Siege, Debug)
- **`src/voice.py`**: TTS engines (ElevenLabs, pyttsx3)
- **`src/vision.py`**: OCR providers (EasyOCR, Tesseract)

### Layer 3: Infrastructure
- **`src/events.py`**: Event bus for async communication
- **`src/analytics.py`**: Usage tracking and cost calculation
- **`src/cache.py`**: Development cache for API responses
- **`src/config.py`**: Configuration management

### Layer 4: Application
- **`main.py`**: Entry point, CLI argument handling
- **`src/bot.py`**: Main controller, hotkey binding, orchestration
- **`src/factory.py`**: Dependency injection container

## Key Design Decisions

1. **Interface-based architecture**: All components implement interfaces for easy swapping and testing
2. **Factory pattern**: Centralizes object creation based on configuration
3. **Event-driven**: Decouples hotkey handlers from business logic
4. **Singleton patterns**: Config, Cache, and Analytics use singletons for global access

