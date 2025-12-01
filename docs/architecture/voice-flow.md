# Voice Generation Flow

This section explains the flow when a user presses the voice trigger hotkey.

## End-to-End Flow

1. **User input**
   - The user presses the F5 hotkey (configured as the voice trigger).
   - The keyboard library running in a separate thread invokes the bound callback.

2. **Event publication**
   - The callback publishes a `TRIGGER_VOICE` event to the event bus.
   - The event bus schedules this event onto the main asyncio loop using its internal queue.

3. **Event handling in the bot**
   - The bot’s main loop awaits events from the queue.
   - When it receives `TRIGGER_VOICE`, it calls `_process_trigger_voice()`.

4. **Voice-oriented message generation**
   - `_process_trigger_voice()` calls `provider.get_message(mode="voice")`.
   - The provider generates a message tailored for spoken output (usually longer and more natural than text chat messages).
   - The provider returns the text to the bot, for example: `"That was an insane clutch bro!"`.

5. **Text-to-speech synthesis**
   - The bot passes the text to the TTS subsystem: `tts.synthesize(text)`.
   - The TTS engine can use one of two backends:
     - **ElevenLabs** (cloud):
       - Sends the text and `voice_id` to the ElevenLabs API.
       - Receives an audio stream (e.g. MP3), saves it to a temporary file.
       - Records analytics such as provider name, character count, and latency.
     - **pyttsx3** (offline):
       - Initializes a local speech engine.
       - Saves synthesized audio directly to a file path.
       - Records the same analytics metrics (provider, characters, latency).
   - In both cases, the TTS layer returns the final audio file path to the bot.

6. **Audio playback and routing**
   - The bot calls the audio player with the generated audio path.
   - The audio player streams the file to the configured output(s):
     - **Single output**: audio is sent only to the virtual cable device that the game uses as a microphone input.
     - **Monitor mode enabled**: audio is streamed both to the virtual cable **and** to the system’s default playback device so the user can hear it.

7. **Cleanup and completion**
   - After playback finishes, the audio player deletes the temporary file.
   - Control returns to the bot, and the voice line has been played in‑game via the virtual cable as if it were a live microphone input.

## Flow Steps

1. **Hotkey Detection**: F5 press detected
2. **Event Publishing**: TRIGGER_VOICE event published
3. **Message Generation**: Provider generates message optimized for voice (longer, more natural)
4. **TTS Synthesis**: 
   - **ElevenLabs**: Cloud API call, high-quality voice
   - **pyttsx3**: Local synthesis, free but robotic
5. **Analytics Tracking**: Track character count, cost, latency
6. **Audio Playback**: 
   - Stream to virtual audio cable (game input)
   - Optionally monitor on default device
7. **Cleanup**: Delete temporary audio file

## Audio Configuration

### Virtual Cable Setup
- **Windows**: VB-Audio Virtual Cable
- **Purpose**: Route audio from bot to game mic input
- **Configuration**: `AUDIO_OUTPUT_DEVICE_NAME` in `.env`

### Monitor Mode
- **Enabled**: `AUDIO_MONITORING=true`
- **Effect**: Hear what the bot says while it plays to game
- **Implementation**: Dual-stream output (virtual cable + default device)

## Cost Considerations

- **ElevenLabs**: ~$0.30 per 1K characters
- **pyttsx3**: Free (offline)
- Analytics tracks all TTS usage and costs in SQLite database

