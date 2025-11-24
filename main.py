"""
Main entry point for the Rainbow Six Siege auto-chat bot application.
Handles setup, initialization, and lifecycle management.
"""
import logging
import sys
import asyncio
import argparse
from src.config import Config
from src.bot import AutoChatBot
from src.input_manager import patch_pydirectinput
from src.factory import get_message_provider, get_chat_typer, get_tts_engine, get_context_observer
from src.events import EventBus
from src.voice import SoundDevicePlayer
from src.logging_config import setup_logging


async def main(verbose: bool = False, dry_run: bool = False) -> None:
    """
    Main application entry point.
    Sets up logging, applies patches, initializes the bot, and starts the main loop.
    
    Args:
        verbose: Enable DEBUG level logging with JSON format
        dry_run: Enable dry-run mode (mock API calls, no actual typing)
    """
    setup_logging(verbose=verbose)
    logger = logging.getLogger(__name__)
    
    if dry_run:
        logger.warning("DRY-RUN MODE ENABLED - No actual API calls or typing will occur")
        Config.DRY_RUN = True
    
    # Apply monkey-patches
    patch_pydirectinput()
    
    try:
        # Start analytics session if enabled
        from src.analytics import get_analytics
        analytics = get_analytics()
        analytics.start_session()
        
        # Assemble dependencies
        event_bus = EventBus()
        provider = get_message_provider(event_bus=event_bus)
        typer = get_chat_typer()
        
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
    finally:
        # End analytics session
        try:
            from src.analytics import get_analytics
            analytics = get_analytics()
            analytics.end_session()
            
            # Show session stats
            stats = analytics.get_session_stats()
            if stats:
                logger.info(f"Session stats: {stats['api_call_count']} API calls, "
                           f"{stats['tts_count']} TTS generations, "
                           f"${stats['total_cost']:.6f} total cost")
        except Exception:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rainbow Six Siege Auto-Chat Bot")
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable DEBUG level logging with JSON format"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Enable dry-run mode (mock API calls, no actual typing)"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(main(verbose=args.verbose, dry_run=args.dry_run))
    except KeyboardInterrupt:
        # Handle Ctrl+C from the event loop runner itself
        pass
