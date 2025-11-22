import os
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """
    Centralized configuration management.
    """
    # General
    TRIGGER_KEY = os.getenv("TRIGGER_KEY", "f6")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "120"))
    LANGUAGE = os.getenv("LANGUAGE", "en").lower()

    # Voice Configuration
    VOICE_TRIGGER_KEY = os.getenv("VOICE_TRIGGER_KEY", "f5")
    AUDIO_OUTPUT_DEVICE_NAME = os.getenv("AUDIO_OUTPUT_DEVICE_NAME")  # None = Default
    AUDIO_OUTPUT_DEVICE_INDEX = os.getenv("AUDIO_OUTPUT_DEVICE_INDEX")
    if AUDIO_OUTPUT_DEVICE_INDEX:
        AUDIO_OUTPUT_DEVICE_INDEX = int(AUDIO_OUTPUT_DEVICE_INDEX)
    
    # Audio Monitoring (Hear what the bot says)
    AUDIO_MONITORING = os.getenv("AUDIO_MONITORING", "true").lower() == "true"

    # TTS Configuration
    # Options: pyttsx3, elevenlabs
    TTS_PROVIDER = os.getenv("TTS_PROVIDER", "pyttsx3").lower()
    
    # ElevenLabs
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM") # Default to Rachel
    ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL", "eleven_monolingual_v1")
    ELEVENLABS_STABILITY = float(os.getenv("ELEVENLABS_STABILITY", "0.5"))
    ELEVENLABS_SIMILARITY_BOOST = float(os.getenv("ELEVENLABS_SIMILARITY_BOOST", "0.75"))


    # ChatGPT / AI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    NEXT_PROMPT_KEY = os.getenv("NEXT_PROMPT_KEY", "f8")
    PREV_PROMPT_KEY = os.getenv("PREV_PROMPT_KEY", "f7")

    # Message Provider
    # Options: fixed, random, chatgpt
    MESSAGE_PROVIDER_TYPE = os.getenv("MESSAGE_PROVIDER", "fixed").lower()
    FIXED_MESSAGE = os.getenv("FIXED_MESSAGE", "Good luck have fun!")
    
    # Typer
    TYPER_TYPE = os.getenv("TYPER_TYPE", "r6").lower()
    OPEN_CHAT_DELAY = float(os.getenv("OPEN_CHAT_DELAY", "0.2"))
    TYPING_INTERVAL = float(os.getenv("TYPING_INTERVAL", "0.01"))

    # Vision / Context Awareness
    # Options: easyocr, tesseract
    VISION_ENGINE = os.getenv("VISION_ENGINE", "easyocr").lower()
    TESSERACT_PATH = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    
    # Regions of Interest (ROIs)
    # Loaded from rois.json
    VISION_ROIS = {}
    
    @classmethod
    def load_rois(cls):
        try:
            with open('rois.json', 'r') as f:
                cls.VISION_ROIS = json.load(f)
        except FileNotFoundError:
            logger.warning("rois.json not found. Vision will be disabled.")
            cls.VISION_ROIS = {}
        except json.JSONDecodeError:
             logger.error("rois.json is invalid JSON.")
             cls.VISION_ROIS = {}

# Load ROIs at startup
Config.load_rois()
