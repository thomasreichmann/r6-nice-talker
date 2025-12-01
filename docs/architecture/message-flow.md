# Message Generation Flow (Text)

This section explains the flow when a user presses the text message hotkey.

## End-to-End Flow

1. **User input**
   - The user presses the F6 hotkey (configured as the text message trigger).
   - The keyboard library running in a separate thread invokes the bound callback.

2. **Event publication**
   - The callback publishes a `TRIGGER_CHAT` event to the event bus.
   - The event bus schedules this event onto the main asyncio loop using its internal queue.

3. **Event handling in the bot**
   - The bot’s main loop awaits events from the queue.
   - When it receives `TRIGGER_CHAT`, it calls `_process_trigger_chat()`.

4. **Optional context gathering**
   - `_process_trigger_chat()` asks the context observer (`get_context()`) for the current game context.
   - The observer may:
     - Capture configured screen ROIs.
     - Run OCR over each ROI.
     - Return a summarized string such as `"KILLFEED: Player eliminated"` or an empty string if no useful context is found.

5. **Message generation request**
   - The bot calls `provider.get_message(mode="text", context=context_string)`.
   - The provider decides how to construct a prompt and which backend to use (e.g. OpenAI).

6. **Cache lookup**
   - Before making an API call, the provider asks the cache:
     - `cache.get(persona, context, mode)`.
   - If there is a **cache hit**, the cached message is returned immediately.

7. **API call and analytics (cache miss path)**
   - If there is a **cache miss**, the provider calls the OpenAI Chat Completions API.
   - The API responds with a generated message and token usage details.
   - The provider records analytics for this call (tokens, cost, latency).
   - The provider stores the result in the cache for future reuse.

8. **Message returned to bot**
   - The provider returns the final text (e.g. `"gg ez"`) to the bot.

9. **Typing into the game**
   - The bot asks the typer to `send("gg ez")`.
   - The typer simulates key presses:
     - Presses the chat key (typically `y` in Rainbow Six Siege).
     - Types the message characters one by one with optional delays.
     - Presses `Enter` to send the message.

10. **Result in-game**
    - The game receives the simulated input, and the message appears in the in‑game chat for all players to see.

## Flow Steps

1. **Hotkey Detection**: Keyboard library (running in separate thread) detects F6 press
2. **Event Publishing**: Thread-safe event publishing to async event bus
3. **Event Consumption**: Bot's main async loop receives event
4. **Context Gathering**: Optional - Observer captures game state via OCR
5. **Cache Check**: Check if we've generated similar message recently
6. **API Call**: If not cached, call OpenAI API
7. **Analytics**: Track token usage and cost
8. **Caching**: Save result for future use
9. **Typing**: Simulate keyboard input to send message to game

## Performance Considerations

- **Cache**: Eliminates redundant API calls (TTL: 24h default)
- **Async**: Non-blocking I/O for API calls and typing
- **Threading**: Keyboard callbacks run in separate threads

