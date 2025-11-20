# Learnings: Building the R6 Nice Talker

*A retrospective for my future self on building GenAI-powered game utilities.*

## The Vision & The Reality
I set out to build a tool that injects positivity (or specific personas) into *Rainbow Six Siege* using OpenAI. What started as a simple script ("press key -> call API -> type result") quickly revealed that even "fun" prototypes require architectural discipline if they are to be maintainable and responsive.

This document outlines what I learned about code organization, prompt engineering, and interacting with finicky game clients.

---

## 1. Code Organization: The "Utils" Trap
**The Mistake:**
In the early stages, I dumped everything into `utils.py` or `main.py`. Input handling, string cleaning, and latency measurement all lived together. This made the code hard to navigate and harder to test.

**The Fix:**
We eventually refactored into a proper modular structure:
- **`input_manager.py`**: Low-level IO specific to the OS/Game (DirectX inputs).
- **`typers.py`**: High-level abstractions (Debug vs. Game).
- **`providers.py`**: The "Brain" logic (Fixed strings vs. AI).
- **`constants.py`**: Configuration data separated from logic.

**Lesson for Next Time:**
Start with **Interfaces** immediately, even for a prototype. Defining `IMessageProvider` and `IChatTyper` early on allowed me to test the bot logic without launching the game (using `DebugTyper` and `FixedMessageProvider`).

## 2. Prompt Engineering for Real-Time "Chat"
Getting an LLM to sound like a gamer in a 5-second window is harder than it looks.

### The Sandwich Technique
We found success using a 3-layer prompt structure:
1.  **Base Instructions (Constant):** Global constraints. "No emojis", "lowercase", "under 120 chars", "no punctuation". This ensures the output is always technically compatible with the game engine.
2.  **Persona (Variable):** The specific "flavor" (e.g., "Reputation Farmer" vs. "Toxic Ash Main").
3.  **Context (Variable):** What just happened (e.g., "We won the round").

### Post-Processing is Mandatory
Trusting the raw LLM output is a mistake.
- **Hashtags:** The model loves adding `#RainbowSix`, but that looks fake in-game.
- **Quotes:** It often wraps responses in quotes.
- **Unicode/Emojis:** Most game chat boxes render these as `[]` or crash.
**Solution:** We implemented strict regex cleaning (`remove_emojis`) immediately after generation.

## 3. Interacting with Game Windows (The DirectX Problem)
Standard Python libraries like `pyautogui` often fail inside 3D games because games read raw hardware interrupts (DirectInput) rather than OS-level signals.

**The Pitfall:**
Trying to use standard keyboard libraries resulted in the game ignoring inputs.

**The Solution:**
We used `pydirectinput`. However, we had to **monkey-patch** it to add safety delays (`safe_keypress`). Games need a key to be "held" for a few milliseconds (frame time) to register; instantaneous 0ms presses often get dropped.

## 4. The "Refactor Phase" Improvements
We did a major cleanup pass that should be standard practice for my future projects:

1.  **Centralized Constants:** Moving prompts and context strings to `constants.py` made tweaking the bot's "personality" possible without scrolling through 200 lines of API logic.
2.  **Input Isolation:** Moving the `patch_pydirectinput` logic to its own file means if I switch to a different game or input library later, I only change one file.
3.  **Docstring Hygiene:** We initially over-documented. I learned that `def get_message(): return message` does *not* need a docstring. It creates noise. Focus documentation on *why* something exists, not just what it does.

## 5. UX & Feedback in Headless Apps
Since the app runs in the background while I play:
- **Audio Feedback is Critical:** I can't see the terminal. Adding `SoundManager` (beeps for success/failure) was the single biggest UX improvement. It tells me if the API call failed or if the persona switched without me Alt-Tabing.
- **Latency Logging:** Wrapping the generation in a `@measure_latency` decorator helped me tune the UX. I learned that if the API takes >2 seconds, the game moment has passed.

## 6. Applied Design Patterns (Universal)
*These principles apply whether you are using Python, Java, TypeScript, or C#.*

### A. Dependency Injection (DI)
**The Problem:**
Our `AutoChatBot` initially created its own `R6SiegeTyper` internally. This meant testing the bot *required* the game to be running, which was painful.

**The Step-by-Step Decision:**
1.  We removed `typer = R6SiegeTyper()` from the `AutoChatBot` constructor.
2.  We changed the constructor to accept `chat_typer: IChatTyper` as an argument.
3.  We moved the creation logic to `main.py`.

**The Result:**
We could now pass a `DebugTyper` (which just `print()`s) during development. This separated the "Bot Logic" from the "Game IO Logic".

### B. The Strategy Pattern
**The Problem:**
We wanted to switch between "Random Pre-written Messages" and "OpenAI Generation" without rewriting the main loop.

**The Step-by-Step Decision:**
1.  We identified the common action: `get_message()`.
2.  We defined an interface `IMessageProvider`.
3.  We implemented it in two ways: `RandomMessageProvider` (Strategy A) and `ChatGPTProvider` (Strategy B).

**The Result:**
The main loop (`bot._execute_macro`) calls `self.provider.get_message()`. It doesn't care if the text comes from a list or a cloud API. This conforms to the **Open/Closed Principle**: we can add a `ClaudeProvider` later without touching `bot.py`.

### C. Single Responsibility Principle (SRP)
**The Problem:**
`utils.py` was becoming a "God Object", handling timing, string regex, AND keyboard inputs.

**The Step-by-Step Decision:**
1.  We audited `utils.py` and asked "What is the reason for this file to change?".
2.  The answer was "Everything", which is wrong.
3.  We extracted `input_manager.py` (changes only on OS/Input updates).
4.  We extracted `constants.py` (changes only on Configuration updates).

**The Result:**
When I need to update the persona prompts, I open `constants.py`. I don't risk accidentally breaking the keyboard input logic because that code is in a completely different file.

### D. Resilience & Graceful Degradation
**The Problem:**
In a live game, if the internet stutters, the bot would crash, killing the process.

**The Step-by-Step Decision:**
1.  We identified "API Calls" as a volatile operation.
2.  We wrapped the specific API call in a `try/except` block *inside* the provider.
3.  We added a fallback: Play an error sound and return a safe "Error" string (or suppress output).

**The Result:**
The application loop is robust. A temporary failure results in audio feedback ("Error Beep"), but the process stays alive for the next attempt.

---

## Checklist for the Next "AI Wrapper" Project
- [ ] **Externalize Prompts:** JSON or YAML file for prompts immediately. Don't hardcode strings.
- [ ] **Interface First:** Define your Source (AI/Data) and Sink (Screen/Chat) as interfaces before writing implementation.
- [ ] **Sanitization:** Never pipe LLM output directly to a system command or input without regex cleaning.
- [ ] **Feedback Loop:** Audio or Overlay feedback is mandatory for full-screen apps.
- [ ] **Config vs Code:** Keep your LLM System Prompts in a config file, not inside the class methods.
