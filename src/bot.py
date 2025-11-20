"""
Main bot application module that controls hotkey bindings and message generation workflow.
"""
import keyboard
import logging
from src.interfaces import IMessageProvider, IChatTyper, ISwitchableMessageProvider
from src.sounds import SoundManager

logger = logging.getLogger(__name__)


class AutoChatBot:
    """
    The main application controller that orchestrates message generation and typing.
    Binds hotkeys to trigger message generation and persona switching.
    
    Args:
        trigger_key (str): The hotkey to trigger message generation.
        message_provider (IMessageProvider): The provider that generates messages.
        chat_typer (IChatTyper): The typer that sends messages to the game.
        next_mode_key (str, optional): Hotkey to switch to next persona.
        prev_mode_key (str, optional): Hotkey to switch to previous persona.
    """
    def __init__(
        self, 
        trigger_key: str, 
        message_provider: IMessageProvider, 
        chat_typer: IChatTyper,
        next_mode_key: str = None,
        prev_mode_key: str = None
    ) -> None:
        self.trigger_key = trigger_key
        self.provider = message_provider
        self.typer = chat_typer
        self.next_mode_key = next_mode_key
        self.prev_mode_key = prev_mode_key
        self.is_running = False

    def _execute_macro(self) -> None:
        """
        Executes the main macro: generates a message and types it into the game.
        Plays audio feedback for success or error states.
        """
        try:
            # Audio Feedback: Operation Started
            SoundManager.play_success()
            
            # Get the content
            msg = self.provider.get_message()
            
            # Send it
            self.typer.send(msg)
        except Exception as e:
            logger.error(f"Error executing macro: {e}", exc_info=True)
            SoundManager.play_error()

    def _next_mode(self) -> None:
        if isinstance(self.provider, ISwitchableMessageProvider):
            self.provider.next_mode()

    def _prev_mode(self) -> None:
        if isinstance(self.provider, ISwitchableMessageProvider):
            self.provider.prev_mode()

    def start(self) -> None:
        """
        Starts the keyboard listener loop and registers all hotkeys.
        Blocks until the user presses ESC or Ctrl+C to exit.
        """
        logger.info("Program started.")
        logger.info(f"Using Provider: {self.provider.__class__.__name__}")
        logger.info(f"Using Typer: {self.typer.__class__.__name__}")
        logger.info(f"Press '{self.trigger_key}' to send message.")
        
        if isinstance(self.provider, ISwitchableMessageProvider):
            logger.info(f"Mode Switching Enabled: Next='{self.next_mode_key}', Prev='{self.prev_mode_key}'")
        
        logger.info("Press 'esc' or Ctrl+C to quit.")
        
        try:
            # Register trigger hotkey
            keyboard.add_hotkey(self.trigger_key, self._execute_macro)
            
            # Register mode switching hotkeys if provider supports it
            if isinstance(self.provider, ISwitchableMessageProvider):
                if self.next_mode_key:
                    keyboard.add_hotkey(self.next_mode_key, self._next_mode)
                if self.prev_mode_key:
                    keyboard.add_hotkey(self.prev_mode_key, self._prev_mode)
            
            # Block until escape
            keyboard.wait('esc')
        except KeyboardInterrupt:
            # This block catches Ctrl+C
            logger.info("Received KeyboardInterrupt. Shutting down...")
        finally:
            self.stop()

    def stop(self) -> None:
        logger.info("Cleaning up...")
        try:
            keyboard.unhook_all()
            logger.info("Hotkeys unhooked.")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
        logger.info("Shutdown complete.")
