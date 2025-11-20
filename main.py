import logging
import sys
from src.config import Config
from src.bot import AutoChatBot
from src.providers import FixedMessageProvider, RandomMessageProvider, ChatGPTProvider
from src.typers import R6SiegeTyper, DebugTyper
from src.utils import patch_pydirectinput

def setup_logging():
    """
    Configures the logging format and level.
    """
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_message_provider():
    provider_type = Config.MESSAGE_PROVIDER_TYPE
    
    if provider_type == 'random':
        return RandomMessageProvider([
            "Good luck have fun!",
            "Hello team!",
            "Nice shot!",
            "gg wp"
        ])
    elif provider_type == 'chatgpt':
        return ChatGPTProvider(
            api_key=Config.OPENAI_API_KEY,
            model=Config.OPENAI_MODEL
        )
    else:
        # Default to fixed
        return FixedMessageProvider(Config.FIXED_MESSAGE)

def get_chat_typer():
    if Config.TYPER_TYPE == 'debug':
        return DebugTyper()
    else:
        return R6SiegeTyper(
            open_chat_delay=Config.OPEN_CHAT_DELAY,
            typing_interval=Config.TYPING_INTERVAL
        )

def main():
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
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
