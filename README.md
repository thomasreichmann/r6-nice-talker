# R6 Nice Talker

A python script that uses AI to generate and type "wholesome" (or edgy, or salty) messages in Rainbow Six Siege chat.

## Features
- **AI-Powered**: Uses OpenAI (ChatGPT) to generate unique, context-aware messages.
- **Persona Switching**: Cycle between personas like "Reputation Farmer", "Preacher", "Salty", etc. using hotkeys.
- **Game Safe**: Simulates human-like keystrokes (holds keys for 50ms) to ensure input registers in-game.
- **Context Aware**: Simulates game events (clutches, losses) to generate relevant banter.
- **Audio Feedback**: Beeps to confirm actions or persona switches so you don't have to tab out.

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

## Usage
-   **F6**: Generate and type a message.
-   **F8**: Next Persona.
-   **F7**: Previous Persona.
-   **ESC**: Quit.

## Customization
Edit `prompts.json` to add your own personas or change the style of existing ones.

