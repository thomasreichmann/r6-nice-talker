import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """
    Centralized configuration management.
    """
    # General
    TRIGGER_KEY = os.getenv("TRIGGER_KEY", "f6")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "120"))

    # Voice Configuration
    VOICE_TRIGGER_KEY = os.getenv("VOICE_TRIGGER_KEY", "f5")
    AUDIO_OUTPUT_DEVICE_NAME = os.getenv("AUDIO_OUTPUT_DEVICE_NAME")  # None = Default
    AUDIO_OUTPUT_DEVICE_INDEX = os.getenv("AUDIO_OUTPUT_DEVICE_INDEX")
    if AUDIO_OUTPUT_DEVICE_INDEX:
        AUDIO_OUTPUT_DEVICE_INDEX = int(AUDIO_OUTPUT_DEVICE_INDEX)
    
    # Audio Monitoring (Hear what the bot says)
    AUDIO_MONITORING = os.getenv("AUDIO_MONITORING", "true").lower() == "true"


    # ChatGPT / AI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    # Swapped logic: F8 is Next, F7 is Prev (as requested)
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
