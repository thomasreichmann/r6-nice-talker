"""
Input management module for handling keyboard inputs.
Provides safe key press functionality and pydirectinput patches.
"""
import time
import logging
import pydirectinput

logger = logging.getLogger(__name__)


def safe_keypress(key: str, duration: float = 0.05) -> None:
    """
    Safely presses a key by holding it down for a specified duration.
    Essential for games that don't register instantaneous inputs.
    
    Args:
        key (str): The key to press (e.g., 'y', 'enter').
        duration (float): How long to hold the key down in seconds. Defaults to 0.05.
    """
    pydirectinput.keyDown(key)
    time.sleep(duration)
    pydirectinput.keyUp(key)


def patch_pydirectinput() -> None:
    """
    Monkey-patches pydirectinput to include a custom 'press_safe' method.
    This allows us to call pydirectinput.press_safe('y') anywhere in the codebase.
    """
    if not hasattr(pydirectinput, 'press_safe'):
        pydirectinput.press_safe = safe_keypress
        logger.info("Monkey-patched pydirectinput with 'press_safe' method.")
