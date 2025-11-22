import logging
import sys
from src.config import Config
from src.providers import FixedMessageProvider, RandomMessageProvider, ChatGPTProvider
from src.typers import R6SiegeTyper, DebugTyper
from src.voice import Pyttsx3TTS, ElevenLabsTTS
from src.vision import TesseractProvider, EasyOCRProvider

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

def get_tts_engine():
    """
    Returns the configured Text-to-Speech engine.
    """
    if Config.TTS_PROVIDER == 'elevenlabs':
        return ElevenLabsTTS(
            api_key=Config.ELEVENLABS_API_KEY,
            voice_id=Config.ELEVENLABS_VOICE_ID,
            model_id=Config.ELEVENLABS_MODEL_ID,
            stability=Config.ELEVENLABS_STABILITY,
            similarity_boost=Config.ELEVENLABS_SIMILARITY_BOOST
        )
    else:
        return Pyttsx3TTS()

def get_context_observer():
    """
    Returns the configured Context Observer (previously just Vision).
    """
    engine = Config.VISION_ENGINE
    
    if engine == 'tesseract':
        return TesseractProvider()
    else:
        # Default to EasyOCR
        return EasyOCRProvider()
