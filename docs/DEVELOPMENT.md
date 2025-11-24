# Development Guide

This guide covers common development workflows, debugging techniques, and best practices for working with R6 Nice Talker.

## Table of Contents

- [Development Tools](#development-tools)
- [Common Workflows](#common-workflows)
- [Development Modes](#development-modes)
- [Debugging Tips](#debugging-tips)
- [Cost Management](#cost-management)
- [Performance Optimization](#performance-optimization)

## Development Tools

### Standalone Testing Tools

Test components in isolation without running the full bot:

#### Test TTS
```bash
# Test pyttsx3 (offline, free)
python tools/test_tts.py --text "Hello world" --provider pyttsx3

# Test ElevenLabs (requires API key)
python tools/test_tts.py --text "Hello world" --provider elevenlabs

# Save output for comparison
python tools/test_tts.py --text "Test" --provider pyttsx3 --save --no-play

# Adjust voice settings
python tools/test_tts.py --text "Fast speech" --provider pyttsx3 --rate 200
```

#### Test Message Generation
```bash
# Dry-run (no API cost)
python tools/test_messages.py --persona Toxic --dry-run

# With custom context
python tools/test_messages.py --persona Wholesome --context "We just won!"

# List all personas
python tools/test_messages.py --list-personas

# Generate for voice mode
python tools/test_messages.py --persona FalleN --mode voice
```

#### Test Vision/OCR
```bash
# Test specific ROI
python tools/test_vision.py --roi killfeed --engine easyocr

# Compare engines
python tools/test_vision.py --compare --save

# List configured ROIs
python tools/test_vision.py --list-rois

# Save processed images for debugging
python tools/test_vision.py --save --no-preview
```

#### Test Typer
```bash
# Dry-run (doesn't actually type)
python tools/test_typer.py --text "test message" --dry-run

# Test timing consistency
python tools/test_typer.py --text "test" --repeat 5

# Custom delays
python tools/test_typer.py --text "slow typing" --interval 0.05 --delay 0.5
```

### GUI Tools

Launch the unified GUI for visual testing and configuration:

```bash
python gui_launcher.py
```

Available tools:
- **Analytics Dashboard**: View costs, usage, trends
- **Config Editor**: Visual `.env` editor with validation
- **Prompt Editor**: Edit personas with live preview
- **Test Suite**: GUI for all testing tools
- **Live Monitor**: Real-time bot monitoring

## Common Workflows

### Workflow 1: Testing New Persona

```bash
# 1. Edit prompts.json (hot-reload enabled)
vim prompts.json

# 2. Test generation without API cost
python tools/test_messages.py --persona MyNewPersona --dry-run

# 3. Test actual generation
python tools/test_messages.py --persona MyNewPersona --context "We lost"

# 4. Test in bot with dry-run
python main.py --dry-run

# 5. Test for real (will cost API tokens)
python main.py
```

### Workflow 2: Adding New TTS Provider

```bash
# 1. Implement ITextToSpeech in src/voice.py
# 2. Add to factory in src/factory.py
# 3. Add config in src/config.py
# 4. Test standalone
python tools/test_tts.py --text "test" --provider mynew

# 5. Check analytics tracking
sqlite3 .analytics.db "SELECT * FROM tts_usage ORDER BY timestamp DESC LIMIT 5;"
```

### Workflow 3: Debugging Vision Issues

```bash
# 1. Configure ROIs visually
python debug_rois.py

# 2. Test OCR on configured ROIs
python tools/test_vision.py --save

# 3. Check saved images in vision_output/
ls -la vision_output/

# 4. Compare engines if accuracy is poor
python tools/test_vision.py --compare --roi problematic_roi

# 5. Adjust preprocessing in src/vision.py if needed
# 6. Re-test
python tools/test_vision.py --roi problematic_roi
```

### Workflow 4: Cost Optimization

```bash
# 1. Enable caching
echo "DEV_CACHE_ENABLED=true" >> .env

# 2. Run bot with caching
python main.py

# 3. Check cache stats
python -c "from src.cache import get_cache; print(get_cache().stats())"

# 4. Check analytics
python gui_launcher.py  # Open Analytics Dashboard

# 5. Export data for analysis
python -c "from src.analytics import get_analytics; get_analytics().export_csv('analytics_export')"
```

## Development Modes

### Dry-Run Mode

Simulates all operations without making actual API calls or typing:

```bash
python main.py --dry-run
```

**What it does:**
- ✅ Loads configuration
- ✅ Binds hotkeys
- ✅ Processes events
- ❌ No OpenAI API calls (returns mock responses)
- ❌ No TTS synthesis (logs what would be synthesized)
- ❌ No keyboard typing (logs what would be typed)

**Use cases:**
- Testing hotkey bindings
- Verifying event flow
- Testing without API costs
- Debugging logic without side effects

### Verbose Mode

Enables DEBUG logging with JSON format:

```bash
python main.py --verbose
```

**Output includes:**
- Full API request/response (sanitized keys)
- Token usage per request
- Timing for all operations
- Cache hits/misses
- Analytics tracking details

**Use cases:**
- Debugging API issues
- Performance profiling
- Understanding system behavior
- Generating logs for bug reports

### Cache Mode

Caches API responses to avoid redundant calls:

```env
# In .env
DEV_CACHE_ENABLED=true
DEV_CACHE_TTL=86400  # 24 hours
```

**How it works:**
- Key: `hash(persona_name + context + mode + language)`
- Storage: `.dev_cache/` directory (JSON files)
- TTL: Configurable (default 24h)
- Automatic cleanup of expired entries

**Cache operations:**
```python
from src.cache import get_cache

cache = get_cache()

# Check stats
stats = cache.stats()
print(f"Valid: {stats['valid_files']}, Expired: {stats['expired_files']}")

# Clear expired
cache.clear_expired()

# Clear all
cache.clear_all()
```

### Hot-Reload Mode

Automatically reloads `prompts.json` when modified:

```env
PROMPTS_HOT_RELOAD=true
```

**How it works:**
- Watches `prompts.json` for file modifications
- Reloads prompts automatically
- Plays sound feedback
- Logs persona changes
- Tries to keep current persona selected

**Use cases:**
- Iterating on persona prompts
- A/B testing different phrasings
- Live adjustments during gameplay

## Debugging Tips

### Enable Full Logging

```bash
# Terminal output
python main.py --verbose 2>&1 | tee bot_debug.log

# Check log file
tail -f bot.log
```

### Debug Specific Component

```python
# In your script or REPL
import logging
logging.basicConfig(level=logging.DEBUG)

# Test just the component
from src.providers import ChatGPTProvider
provider = ChatGPTProvider(api_key="sk-...")
```

### Common Issues

#### Issue: "No module named 'src'"
**Solution**: Run from project root, not from subdirectory
```bash
cd /path/to/r6-nice-talker
python main.py
```

#### Issue: OpenAI API errors
**Debug steps:**
1. Check API key: `echo $OPENAI_API_KEY` or check `.env`
2. Verify key is valid: Test at https://platform.openai.com/playground
3. Check quota/billing
4. Run with verbose: `python main.py --verbose`

#### Issue: TTS not working
**Debug steps:**
```bash
# Test TTS standalone
python tools/test_tts.py --text "test" --provider pyttsx3

# List audio devices
python list_devices.py

# Check virtual cable configuration
python -c "import sounddevice as sd; print(sd.query_devices())"
```

#### Issue: Vision not detecting text
**Debug steps:**
```bash
# Save images to inspect
python tools/test_vision.py --save

# Check preprocessing (look at vision_output/*_processed.png)
# Adjust threshold in src/vision.py if needed

# Compare engines
python tools/test_vision.py --compare --roi problematic_roi
```

### Using DebugTyper

For testing without typing into game:

```env
# In .env
TYPER_TYPE=debug
```

Now all messages are logged instead of typed.

### Inspect Analytics Database

```bash
# Open database
sqlite3 .analytics.db

# View sessions
SELECT * FROM sessions ORDER BY start_time DESC LIMIT 5;

# View API calls
SELECT provider, model, tokens_total, cost, timestamp 
FROM api_calls 
ORDER BY timestamp DESC 
LIMIT 10;

# Total cost by provider
SELECT provider, SUM(cost) as total_cost, COUNT(*) as call_count
FROM api_calls
GROUP BY provider;

# TTS usage
SELECT provider, SUM(char_count) as total_chars, SUM(cost) as total_cost
FROM tts_usage
GROUP BY provider;
```

## Cost Management

### Track Costs

```bash
# Start bot (analytics auto-enabled)
python main.py

# View costs in GUI
python gui_launcher.py  # → Analytics Dashboard

# Or query database
sqlite3 .analytics.db "SELECT SUM(cost) FROM api_calls WHERE date(timestamp) = date('now');"
```

### Minimize Costs

1. **Use Cache**: Enable `DEV_CACHE_ENABLED=true`
2. **Use Dry-Run**: Test with `--dry-run` first
3. **Use pyttsx3**: Free TTS for development
4. **Use gpt-4o-mini**: Cheaper than GPT-4 (set in `OPENAI_MODEL`)
5. **Test Standalone**: Use tools instead of full bot

### Cost Estimates

| Operation | Provider | Typical Cost | Configuration |
|-----------|----------|--------------|---------------|
| Text message | OpenAI (gpt-4o-mini) | ~$0.0001 | 50 input + 20 output tokens |
| Voice message | OpenAI (gpt-4o-mini) | ~$0.0002 | 80 input + 40 output tokens |
| TTS (pyttsx3) | Local | $0 | Free, offline |
| TTS (ElevenLabs) | Cloud | ~$0.006 | 20 characters @ $0.30/1k |
| OCR | Local | $0 | Free, offline |

**Daily usage example:**
- 50 messages/day × $0.0001 = $0.005/day
- 10 voice lines/day × ($0.0002 + $0.006) = $0.062/day
- **Total: ~$0.067/day** or **$2/month**

## Performance Optimization

### Reduce Latency

1. **Use GPU for EasyOCR**:
```python
# In src/vision.py
self.reader = easyocr.Reader(['en'], gpu=True)
```

2. **Optimize ROIs**:
- Use smallest possible regions
- Reduce number of ROIs
- Disable vision if not needed

3. **Faster Model**:
```env
OPENAI_MODEL=gpt-4o-mini  # Faster than gpt-4
```

### Reduce Memory Usage

1. **Use Tesseract instead of EasyOCR**:
```env
VISION_ENGINE=tesseract
```

2. **Disable hot-reload in production**:
```env
PROMPTS_HOT_RELOAD=false
```

### Profile Performance

```bash
# Run with timing info
python main.py --verbose 2>&1 | grep "latency\|took\|elapsed"

# Check analytics
sqlite3 .analytics.db "SELECT AVG(latency_ms) FROM api_calls;"
```

## Advanced Topics

### Custom Context Providers

Implement `IContextObserver` for custom context sources:

```python
class DiscordListener(IContextObserver):
    def get_context(self) -> str:
        # Read Discord chat, return recent messages
        return "Discord: Player said 'gg'"
```

### Multi-Language Support

Add new language in `src/constants.py`:

```python
SYSTEM_PROMPTS = {
    "en": "...",
    "pt-br": "...",
    "fr": "..."  # Add French
}

USER_PROMPT_TEMPLATES = {
    "en": {...},
    "pt-br": {...},
    "fr": {...}  # Add French templates
}
```

Update `prompts.json`:
```json
{
  "name": "Toxic",
  "prompts": {
    "en": "...",
    "pt-br": "...",
    "fr": "..."
  }
}
```

### Analytics Export & Visualization

```bash
# Export to CSV
python -c "from src.analytics import get_analytics; get_analytics().export_csv('export')"

# Visualize with pandas
python
>>> import pandas as pd
>>> df = pd.read_csv('export/api_calls.csv')
>>> df.groupby('provider')['cost'].sum()
```

## Getting Help

- **Check logs**: `tail -f bot.log`
- **Run health check**: `python -m src.health_check`
- **Use verbose mode**: `python main.py --verbose`
- **Test standalone**: Use `tools/test_*.py` scripts
- **Check analytics**: `python gui_launcher.py`
- **Open issue**: Include logs, config (sanitized), steps to reproduce

