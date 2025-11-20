"""
Main entry point for the Rainbow Six Siege auto-chat bot application.
Handles setup, initialization, and lifecycle management.
"""
import logging
import sys
from src.config import Config
from src.bot import AutoChatBot
from src.input_manager import patch_pydirectinput
from src.factory import setup_logging, get_message_provider, get_chat_typer


def main() -> None:
    """
    Main application entry point.
    Sets up logging, applies patches, initializes the bot, and starts the main loop.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Apply monkey-patches
    patch_pydirectinput()
    
    try:
        # Assemble dependencies
        provider = get_message_provider()
        typer = get_chat_typer()
        
        app = AutoChatBot(
            trigger_key=Config.TRIGGER_KEY,
            message_provider=provider,
            chat_typer=typer,
            next_mode_key=Config.NEXT_PROMPT_KEY,
            prev_mode_key=Config.PREV_PROMPT_KEY
        )
        
        app.start()
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
