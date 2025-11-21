# R6 Nice Talker

A python script that uses AI to generate and type "wholesome" (or edgy, or salty) messages in Rainbow Six Siege chat.

## Features
- **AI-Powered**: Uses OpenAI (ChatGPT) to generate unique, context-aware messages.
- **Persona Switching**: Cycle between personas like "Reputation Farmer", "Preacher", "Salty", etc. using hotkeys.
- **Game Safe**: Simulates human-like keystrokes (holds keys for 50ms) to ensure input registers in-game.
- **Context Aware**: Simulates game events (clutches, losses) to generate relevant banter.
- **Audio Feedback**: Beeps to confirm actions or persona switches so you don't have to tab out.
- **Voice Injection**: Text-to-Speech output directly into the game's voice chat via Virtual Cable.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure**:
    -   Copy `env.example` to `.env`.
    -   Add your `OPENAI_API_KEY`.
    -   (Optional) Customize `TRIGGER_KEY` (default F6) or `NEXT_PROMPT_KEY` (default F8).

3.  **Run**:
    -   **Must run as Administrator** to interact with the game window.
    ```bash
    python main.py
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

4.  **Usage**:
    -   Press `F5` (default) to generate and speak a message into the voice chat.
    -   **Note**: The bot plays the audio into the virtual microphone. You may need to hold your Push-to-Talk key in-game while the bot is speaking (unless you use Open Mic or bind the bot to also hold the PTT key - *future feature*).

## Usage
-   **F6**: Generate and type a message.
-   **F5**: Generate and speak a message.
-   **F8**: Next Persona.
-   **F7**: Previous Persona.
-   **ESC**: Quit.

## Customization
Edit `prompts.json` to add your own personas or change the style of existing ones.

## Learnings & Architecture
This project served as a playground for learning how to build robust GenAI wrappers for real-time applications. 
Check out [LEARNINGS.md](./LEARNINGS.md) for a deep dive into the architectural patterns (Strategy, DI), prompt engineering techniques, and pitfalls encountered during development.
