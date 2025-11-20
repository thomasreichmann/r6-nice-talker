"""
Constants module containing prompts, game contexts, and other configuration strings.
"""

# Base system prompt used by all ChatGPT personas
BASE_SYSTEM_PROMPT = (
    "You are a player in a Rainbow Six Siege match. "
    "Write a single, short in-game chat message (under 120 chars). "
    "Adopt the vernacular of a digital native gamer (informal, rapid-fire, low-effort typing). "
    "Use text-based emoticons if needed, but never emojis. "
    "Write like a stream of consciousness or Twitch chat. Avoid punctuation and uppercase letters unless for emphasis. "
    "Never use formal greetings like 'Hey team' or 'Hello'. "
    "Your response must strictly follow the style of the assigned Persona."
)

# List of possible game scenarios to provide context to AI
GAME_CONTEXTS = [
    "We just won the round comfortably.",
    "We lost the round but it was close.",
    "We got destroyed this round.",
    "A teammate just clutched a 1v3.",
    "Someone on our team failed a 1v1.",
    "The match just started.",
    "It's match point for us.",
    "It's match point for the enemy.",
    "A teammate accidentally team-killed.",
    "The enemy team is trash talking.",
    "It's quiet, nobody is talking.",
    "We are rushing the objective.",
    "We are camping the objective.",
    "A teammate is AFK.",
    "Someone made a funny mistake."
]
