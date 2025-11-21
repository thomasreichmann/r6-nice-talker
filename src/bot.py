"""
Main bot application module that controls hotkey bindings and message generation workflow.
"""
import keyboard
import logging
import asyncio
from src.interfaces import IMessageProvider, IChatTyper, ISwitchableMessageProvider, ITextToSpeech, IAudioPlayer
from src.sounds import SoundManager
from src.events import EventBus, Event, EventType

logger = logging.getLogger(__name__)


class AutoChatBot:
    """
    The main application controller that orchestrates message generation and typing/speaking.
    Binds hotkeys to trigger message generation and persona switching.
    
    Args:
        trigger_key (str): The hotkey to trigger message generation (typing).
        voice_trigger_key (str): The hotkey to trigger message generation (voice).
        message_provider (IMessageProvider): The provider that generates messages.
        chat_typer (IChatTyper): The typer that sends messages to the game.
        event_bus (EventBus): The event bus for async event communication.
        tts_engine (ITextToSpeech, optional): The TTS engine for voice generation.
        audio_player (IAudioPlayer, optional): The player for voice playback.
        next_mode_key (str, optional): Hotkey to switch to next persona.
        prev_mode_key (str, optional): Hotkey to switch to previous persona.
    """
    def __init__(
        self, 
        trigger_key: str, 
        voice_trigger_key: str,
        message_provider: IMessageProvider, 
        chat_typer: IChatTyper,
        event_bus: EventBus,
        tts_engine: ITextToSpeech = None,
        audio_player: IAudioPlayer = None,
        next_mode_key: str = None,
        prev_mode_key: str = None
    ) -> None:
        self.trigger_key = trigger_key
        self.voice_trigger_key = voice_trigger_key
        self.provider = message_provider
        self.typer = chat_typer
        self.event_bus = event_bus
        self.tts_engine = tts_engine
        self.audio_player = audio_player
        self.next_mode_key = next_mode_key
        self.prev_mode_key = prev_mode_key
        self.is_running = False

    async def _process_trigger_chat(self) -> None:
        """
        Handles the TRIGGER_CHAT event: generates a message and types it.
        """
        try:
            # Audio Feedback: Operation Started
            SoundManager.play_success()
            
            # Get the content (awaitable now)
            msg = await self.provider.get_message()
            
            # Send it (awaitable now)
            await self.typer.send(msg)
        except Exception as e:
            logger.error(f"Error executing chat macro: {e}", exc_info=True)
            SoundManager.play_error()

    async def _process_trigger_voice(self) -> None:
        """
        Handles the TRIGGER_VOICE event: generates a message, converts to audio, and plays it.
        """
        if not self.tts_engine or not self.audio_player:
            logger.warning("Voice trigger received but TTS/Audio components are missing.")
            SoundManager.play_error()
            return

        try:
            # Audio Feedback: Operation Started
            SoundManager.play_success()
            
            # Get the content
            msg = await self.provider.get_message()
            
            # Synthesize
            audio_path = await self.tts_engine.synthesize(msg)
            if not audio_path:
                logger.error("TTS failed to generate audio.")
                SoundManager.play_error()
                return

            # Play
            await self.audio_player.play(audio_path)
            
        except Exception as e:
            logger.error(f"Error executing voice macro: {e}", exc_info=True)
            SoundManager.play_error()

    def _trigger_chat_callback(self) -> None:
        """Callback for the keyboard listener (runs in thread). Publishes event."""
        self.event_bus.publish(Event(EventType.TRIGGER_CHAT))

    def _trigger_voice_callback(self) -> None:
        """Callback for the keyboard listener (runs in thread). Publishes event."""
        self.event_bus.publish(Event(EventType.TRIGGER_VOICE))

    def _next_mode_callback(self) -> None:
        """Callback for the keyboard listener (runs in thread). Publishes event."""
        self.event_bus.publish(Event(EventType.NEXT_PERSONA))

    def _prev_mode_callback(self) -> None:
        """Callback for the keyboard listener (runs in thread). Publishes event."""
        self.event_bus.publish(Event(EventType.PREV_PERSONA))

    def _process_next_mode(self) -> None:
        if isinstance(self.provider, ISwitchableMessageProvider):
            self.provider.next_mode()

    def _process_prev_mode(self) -> None:
        if isinstance(self.provider, ISwitchableMessageProvider):
            self.provider.prev_mode()

    async def _consume_events(self) -> None:
        """
        Main event loop consumer. Waits for events and dispatches them.
        """
        logger.info("Event consumer loop started.")
        self.is_running = True
        while self.is_running:
            try:
                event = await self.event_bus.get()
                logger.debug(f"Received event: {event.type}")
                
                if event.type == EventType.TRIGGER_CHAT:
                    await self._process_trigger_chat()
                elif event.type == EventType.TRIGGER_VOICE:
                    await self._process_trigger_voice()
                elif event.type == EventType.NEXT_PERSONA:
                    self._process_next_mode()
                elif event.type == EventType.PREV_PERSONA:
                    self._process_prev_mode()
                elif event.type == EventType.SHUTDOWN:
                    self.is_running = False
                    break
            except asyncio.CancelledError:
                logger.info("Event consumer cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in event loop: {e}", exc_info=True)

    async def start(self) -> None:
        """
        Starts the bot, registers hotkeys, and runs the event loop.
        """
        logger.info("Program started.")
        logger.info(f"Using Provider: {self.provider.__class__.__name__}")
        logger.info(f"Using Typer: {self.typer.__class__.__name__}")
        if self.tts_engine:
            logger.info(f"Using TTS: {self.tts_engine.__class__.__name__}")
        
        logger.info(f"Press '{self.trigger_key}' to type message.")
        logger.info(f"Press '{self.voice_trigger_key}' to speak message.")
        
        if isinstance(self.provider, ISwitchableMessageProvider):
            logger.info(f"Mode Switching Enabled: Next='{self.next_mode_key}', Prev='{self.prev_mode_key}'")
        
        logger.info("Press Ctrl+C to quit.")
        
        try:
            # Register trigger hotkeys
            keyboard.add_hotkey(self.trigger_key, self._trigger_chat_callback)
            keyboard.add_hotkey(self.voice_trigger_key, self._trigger_voice_callback)
            
            # Register mode switching hotkeys if provider supports it
            if isinstance(self.provider, ISwitchableMessageProvider):
                if self.next_mode_key:
                    keyboard.add_hotkey(self.next_mode_key, self._next_mode_callback)
                if self.prev_mode_key:
                    keyboard.add_hotkey(self.prev_mode_key, self._prev_mode_callback)
            
            # Hook cleanup to 'esc' -> REMOVED per user request
            # keyboard.add_hotkey('esc', lambda: self.event_bus.publish(Event(EventType.SHUTDOWN)))

            # Run event consumer
            await self._consume_events()
            
        except asyncio.CancelledError:
            logger.info("Bot task cancelled.")
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
