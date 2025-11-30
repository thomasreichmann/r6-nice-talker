# Future Roadmap: R6 Nice Talker

*A strategic outlook on evolving this project from a "Macro Script" to a "True AI Assistant".*

## The Vision
Currently, the bot is **reactive** to user input but **blind** to the game state. It relies on the user pressing a button and randomness to simulate context ("We won", "We lost").
The ultimate version of this tool is an **Observer**: It watches the game, understands the score, sees the killfeed, and automatically generates relevant commentary without manual triggers.

---

## Priority 1: True Context Awareness (The "Eyes" Upgrade)
**Impact:** 🚀 Critical | **Difficulty:** 🔥 High

The biggest limitation is that the bot "hallucinates" context. It says "Nice clutch!" when we might have just lost.

### Proposed Implementation:
1.  **Optical Character Recognition (OCR):**
    -   Use `pytesseract` or `EasyOCR` to capture the scoreboard/round timer region.
    -   Detect "Round Won/Lost" banners.
2.  **Killfeed Monitoring:**
    -   Watch the killfeed area. If "PlayerName" (User) appears in the killfeed, trigger a specific "Taunt" or "Apology" persona automatically.
3.  **LLM Vision (Experimental):**
    -   Instead of text OCR, take a screenshot and send it to `gpt-4o` or `llava` with the prompt: *"Describe the game state based on the UI."* (High latency risk, but high accuracy).

## Priority 2: Local LLMs (The "Speed & Privacy" Upgrade)
**Impact:** ⭐ High | **Difficulty:** ⚖️ Medium

Dependency on OpenAI introduces latency (~2s) and cost. For a chat bot, we don't need GPT-4 reasoning capabilities.

### Proposed Implementation:
1.  **Ollama / Llama.cpp Integration:**
    -   Replace `ChatGPTProvider` with a `LocalLLMProvider`.
    -   Use 7B or 8B parameter models (e.g., `Llama-3-8B-Quantized`) running locally.
2.  **Benefit:**
    -   **Zero Cost**: No per-token fees.
    -   **Uncensored Models**: Gamer chat often triggers OpenAI's safety filters. Local models can be "spicier" (within reason).
    -   **Speed**: On a decent GPU, inference can be <500ms.

## Priority 3: Desktop GUI (The "UX" Upgrade)
**Impact:** 🎨 Medium | **Difficulty:** ⚖️ Medium

Running a CLI as Administrator is intimidating and lacks visibility.

### Proposed Implementation:
1.  **System Tray Application:**
    -   Use `pystray` or `PyQt6`.
    -   Minimize to tray.
    -   Right-click to switch personas visually.
2.  **Overlay (Advanced):**
    -   A transparent overlay (using DirectX hooks or a transparent window) that shows *what* the bot is about to type *before* it presses Enter.
    -   Allows the user to "Veto" a message with a hotkey cancellation.

## Priority 4: Multi-Game Support
**Impact:** 🔄 Low (Expansion) | **Difficulty:** 📉 Low

The architecture is already modular (`IChatTyper`). Expanding to other games is trivial code-wise but requires specific tuning.

### Potential Targets:
-   **Counter-Strike 2**: Console-based chat makes input injection easier.
-   **Valorant**: High anti-cheat sensitivity (Vanguard). Might require hardware-level input simulation (Arduino/Raspberry Pi Zero HID) to avoid bans.
-   **League of Legends**: Standard chat box, easy to implement.
