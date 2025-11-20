import random

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

def get_random_context() -> str:
    """Returns a random game scenario to inspire the AI."""
    return random.choice(GAME_CONTEXTS)

