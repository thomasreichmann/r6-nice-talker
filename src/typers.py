import pydirectinput
import time
import logging
from src.interfaces import IChatTyper
from src.config import Config

logger = logging.getLogger(__name__)

class R6SiegeTyper(IChatTyper):
    """
    Implements the specific typing logic for Rainbow Six Siege.
    """
    def __init__(self, open_chat_delay: float = 0.2, typing_interval: float = 0.01):
        self.open_chat_delay = open_chat_delay
        self.typing_interval = typing_interval
        self.max_length = Config.MAX_MESSAGE_LENGTH
        
        # Configure global pydirectinput settings
        pydirectinput.FAILSAFE = False
        pydirectinput.PAUSE = 0.0

    def send(self, message: str) -> None:
        # Validation: Truncate message if too long
        final_message = message
        if len(final_message) > self.max_length:
            logger.warning(f"Message too long ({len(final_message)} chars). Truncating to {self.max_length}.")
            final_message = final_message[:self.max_length]
            
        logger.info(f"Sending message: {final_message}")
        
        # 1. Press 'y' to open chat
        # We use our monkey-patched 'press_safe' method!
        pydirectinput.press_safe('y')
        
        # 2. Wait for UI to open
        time.sleep(self.open_chat_delay)
        
        # 3. Type the message
        # Using write() with auto_shift=True is required for pydirectinput-rgx to handle 
        # symbols (like !) and capitals correctly.
        try:
            pydirectinput.write(final_message, interval=self.typing_interval, auto_shift=True)
        except TypeError:
             # Fallback if older version without auto_shift is installed, though requirements specify rgx
             logger.warning("auto_shift not supported in this pydirectinput version. Update to pydirectinput-rgx.")
             pydirectinput.write(final_message, interval=self.typing_interval)
        
        # 4. Short delay before enter
        time.sleep(0.1)
        
        # 5. Send
        pydirectinput.press_safe('enter')

class DebugTyper(IChatTyper):
    """
    Just prints to console. Useful for testing without game running.
    """
    def send(self, message: str) -> None:
        logger.debug(f"[DEBUG] Opening Chat -> Typing: '{message}' -> Enter")
