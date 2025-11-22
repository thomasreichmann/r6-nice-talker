"""
Main entry point for the Rainbow Six Siege auto-chat bot application.
Handles setup, initialization, and lifecycle management.
"""
import logging
import sys
import asyncio
from src.config import Config
from src.bot import AutoChatBot
from src.input_manager import patch_pydirectinput
from src.factory import setup_logging, get_message_provider, get_chat_typer, get_tts_engine, get_context_observer
from src.events import EventBus
from src.voice import SoundDevicePlayer


async def main() -> None:
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
        event_bus = EventBus()
        
        # Voice dependencies
        tts_engine = get_tts_engine()
        audio_player = SoundDevicePlayer(
            device_name=Config.AUDIO_OUTPUT_DEVICE_NAME,
            device_index=Config.AUDIO_OUTPUT_DEVICE_INDEX,
            monitor=Config.AUDIO_MONITORING
        )
        
        # Context/Observer dependencies
        context_observer = get_context_observer()
        
        logger.info(f"TTS Engine: {tts_engine.__class__.__name__}")
        logger.info(f"Context Observer: {context_observer.__class__.__name__}")
        
        app = AutoChatBot(
            trigger_key=Config.TRIGGER_KEY,
            voice_trigger_key=Config.VOICE_TRIGGER_KEY,
            message_provider=provider,
            chat_typer=typer,
            event_bus=event_bus,
            context_observer=context_observer,
            tts_engine=tts_engine,
            audio_player=audio_player,
            next_mode_key=Config.NEXT_PROMPT_KEY,
            prev_mode_key=Config.PREV_PROMPT_KEY
        )
        
        await app.start()
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C from the event loop runner itself
        pass
