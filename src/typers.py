"""
Chat typer implementations for sending messages to games.
Handles keyboard input simulation and game-specific chat interactions.
"""
import pydirectinput
import asyncio
import logging
from src.interfaces import IChatTyper
from src.config import Config

logger = logging.getLogger(__name__)


class R6SiegeTyper(IChatTyper):
    """
    Implements the specific typing logic for Rainbow Six Siege.
    Opens chat with 'y', types the message, and presses Enter.
    
    Args:
        open_chat_delay (float): Delay after opening chat before typing (default: 0.2s).
        typing_interval (float): Delay between each keystroke (default: 0.01s).
    """
    def __init__(self, open_chat_delay: float = 0.2, typing_interval: float = 0.01) -> None:
        self.open_chat_delay = open_chat_delay
        self.typing_interval = typing_interval
        self.max_length = Config.MAX_MESSAGE_LENGTH
        
        # Configure global pydirectinput settings
        pydirectinput.FAILSAFE = False
        pydirectinput.PAUSE = 0.0\
        
    async def send(self, message: str) -> None:
        """
        Sends a message to Rainbow Six Siege chat.
        Opens chat, types the message character by character, and presses Enter.
        
        Args:
            message (str): The message to send in chat.
        """
        # DRY-RUN mode: just log
        if Config.DRY_RUN:
            logger.info(f"[DRY-RUN] Would type in chat: '{message}'")
            logger.info(f"[DRY-RUN] Actions: Press 'y' -> Wait {self.open_chat_delay}s -> Type '{message}' -> Press 'enter'")
            return
        
        # Validation: Truncate message if too long
        final_message = message
        if len(final_message) > self.max_length:
            logger.warning(f"Message too long ({len(final_message)} chars). Truncating to {self.max_length}.")
            final_message = final_message[:self.max_length]
            
        logger.info(f"Sending message: {final_message}")
        
        # 1. Press 'y' to open chat
        # We use our monkey-patched 'press_safe' method!
        # Note: pydirectinput calls are blocking, but quick. 
        # In a pure async world we might run this in an executor, 
        # but for now calling it directly is acceptable as it holds the GIL anyway.
        pydirectinput.press_safe('y')
        
        # 2. Wait for UI to open
        await asyncio.sleep(self.open_chat_delay)
        
        # 3. Type the message
        # Using write() with auto_shift=True is required for pydirectinput-rgx to handle 
        # symbols (like !) and capitals correctly.
        try:
            # pydirectinput.write is blocking. Since typing takes time (0.01 * chars), 
            # it might block the loop for ~1 second for long messages.
            # This is generally acceptable for this app, but strictly could be offloaded.
            pydirectinput.write(final_message, interval=self.typing_interval, auto_shift=True)
        except TypeError:
             # Fallback if older version without auto_shift is installed, though requirements specify rgx
             logger.warning("auto_shift not supported in this pydirectinput version. Update to pydirectinput-rgx.")
             pydirectinput.write(final_message, interval=self.typing_interval)
        
        # 4. Short delay before enter
        await asyncio.sleep(0.1)
        
        # 5. Send
        pydirectinput.press_safe('enter')


class DebugTyper(IChatTyper):
    """
    Debug typer that prints messages to console instead of sending to game.
    Useful for testing without the game running.
    """
    async def send(self, message: str) -> None:
        """
        Prints the message to debug log instead of sending to game.
        
        Args:
            message (str): The message to log.
        """
        logger.debug(f"[DEBUG] Opening Chat -> Typing: '{message}' -> Enter")
