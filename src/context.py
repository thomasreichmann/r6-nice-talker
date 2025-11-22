"""
Context module for providing game scenario information to message generation.
"""
import random
from src.constants import GAME_CONTEXTS
from src.config import Config


def get_random_context(language: str = None) -> str:
    """
    Returns a random game context string in the specified language.
    
    Args:
        language (str, optional): Language code (e.g., 'en', 'pt-br'). 
                                  Defaults to Config.LANGUAGE if not provided.
    """
    if language is None:
        language = Config.LANGUAGE
        
    contexts = GAME_CONTEXTS.get(language, GAME_CONTEXTS["en"])
    return random.choice(contexts)
