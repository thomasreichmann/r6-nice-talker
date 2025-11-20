"""
Context module for providing game scenario information to message generation.
"""
import random
from src.constants import GAME_CONTEXTS


def get_random_context() -> str:
    return random.choice(GAME_CONTEXTS)

