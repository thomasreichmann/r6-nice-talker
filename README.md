# R6 Nice Talker

A python script that uses AI to generate and type "wholesome" (or edgy, or salty) messages in Rainbow Six Siege chat.

## Features
- **AI-Powered**: Uses OpenAI (ChatGPT) to generate unique, context-aware messages.
- **Persona Switching**: Cycle between personas like "Reputation Farmer", "Preacher", "Salty", etc. using hotkeys.
- **Game Safe**: Simulates human-like keystrokes (holds keys for 50ms) to ensure input registers in-game.
- **Context Aware**: Simulates game events (clutches, losses) to generate relevant banter.
- **Audio Feedback**: Beeps to confirm actions or persona switches so you don't have to tab out.
- **Voice Injection**: Text-to-Speech output directly into the game's voice chat via Virtual Cable.
- **TUI Mode**: Optional terminal-based UI for real-time monitoring (use `--tui` flag).

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure**:
    -   Copy `env.example` to `.env`.
    -   Add your `OPENAI_API_KEY`.
    -   (Optional) Customize `TRIGGER_KEY` (default F6) or `NEXT_PROMPT_KEY` (default F8).

3.  **Language Support**:
    -   By default, the bot speaks English (`en`).
    -   To change to Portuguese, update `.env`:
        ```env
        LANGUAGE=pt-br
        ```

4.  **Run**:
    -   **Must run as Administrator** to interact with the game window.
    ```bash
    # Console mode (default)
    python main.py
    
    # TUI mode (terminal UI with real-time monitoring)
    python main.py --tui
    ```

### Voice Injection Setup

To play AI-generated voice lines directly into the game's voice chat:

1.  **Install a Virtual Audio Cable**:
    -   Download and install [VB-Cable](https://vb-audio.com/Cable/) (or similar).
    -   This creates a virtual input ("CABLE Input") and output ("CABLE Output").

2.  **Configure Game Audio**:
    -   In Rainbow Six Siege settings, set **Voice Chat Record Mode** to "Push to Talk" (or "Open" if you dare).
    -   Set **Voice Chat Input Device** to "CABLE Output".

3.  **Configure Bot Output**:
    -   Run the device discovery tool to find your virtual cable's exact name:
        ```bash
        python list_devices.py
        ```
    -   Update your `.env` file with the device name:
        ```env
        AUDIO_OUTPUT_DEVICE_NAME="CABLE Input (VB-Audio Virtual Cable)"
        ```
    -   Alternatively, you can use the device index (`AUDIO_OUTPUT_DEVICE_INDEX`), but names are more reliable.

### Text-to-Speech Configuration

You can choose between the built-in offline TTS (pyttsx3) or high-quality AI voices (ElevenLabs).

**Option 1: Offline (Default)**
- Uses your system's installed TTS voices.
- Fast, free, but robotic.
- Configuration in `.env`:
  ```env
  TTS_PROVIDER=pyttsx3
  ```

**Option 2: ElevenLabs (High Quality)**
- Uses AI generated voices.
- Requires an API key.
- Configuration in `.env`:
  ```env
  TTS_PROVIDER=elevenlabs
  ELEVENLABS_API_KEY=your_api_key
  ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
  ```
  - `ELEVENLABS_VOICE_ID` can be found in the VoiceLab on their website.

### Usage (Voice)

1.  Press `F5` (default) to generate and speak a message into the voice chat.
2.  **Note**: The bot plays the audio into the virtual microphone. You may need to hold your Push-to-Talk key in-game while the bot is speaking.

## Usage

### Running the Bot

**Console Mode (Default)**:
```bash
python main.py
```

**TUI Mode (Terminal UI)**:
```bash
python main.py --tui
```

The TUI provides real-time monitoring of:
- Bot status and components
- Current persona and hotkeys
- Session statistics (API calls, costs, latency)
- Event log with timestamps

Press `q` or `Ctrl+C` to exit TUI mode.

### Hotkeys
-   **F6**: Generate and type a message.
-   **F5**: Generate and speak a message.
-   **F8**: Next Persona.
-   **F7**: Previous Persona.
-   **Ctrl+C**: Quit.

## Customization
Edit `prompts.json` to add your own personas or change the style of existing ones.

## Documentation

- **[Development Guide](./docs/development.md)** - Testing tools, debugging, and cost management
- **[TUI Guide](./docs/tui.md)** - Terminal User Interface features and usage
- **[Architecture](./docs/architecture/)** - Component diagrams and flow documentation
- **[Learnings](./docs/learnings.md)** - Design patterns and lessons learned
- **[Roadmap](./docs/roadmap.md)** - Future features and enhancements
