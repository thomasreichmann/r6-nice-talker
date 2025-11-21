from abc import ABC, abstractmethod
from typing import Any

class IMessageProvider(ABC):
    """
    Interface for providing messages to be sent.
    """
    @abstractmethod
    async def get_message(self) -> str:
        """Returns the next message to be sent."""
        pass

class ISwitchableMessageProvider(IMessageProvider):
    """
    Interface for a provider that has multiple modes or personas (e.g. ChatGPT prompts).
    """
    @abstractmethod
    def next_mode(self) -> None:
        """Switch to the next available mode/persona."""
        pass

    @abstractmethod
    def prev_mode(self) -> None:
        """Switch to the previous available mode/persona."""
        pass

    @abstractmethod
    def get_current_mode_name(self) -> str:
        """Returns the name of the currently active mode/persona."""
        pass

class IChatTyper(ABC):
    """
    Interface for handling the physical typing/sending of the message.
    """
    @abstractmethod
    async def send(self, message: str) -> None:
        """
        Handles the logic of opening chat, typing, and pressing enter.
        """
        pass

class ITextToSpeech(ABC):
    """
    Interface for converting text to speech audio.
    """
    @abstractmethod
    async def synthesize(self, text: str) -> Any:
        """
        Converts text to speech.
        
        Args:
            text (str): The text to convert.
            
        Returns:
            Any: The audio data or path to the audio file.
        """
        pass

class IAudioPlayer(ABC):
    """
    Interface for playing audio data.
    """
    @abstractmethod
    async def play(self, source: Any) -> None:
        """
        Plays the provided audio source.
        
        Args:
            source (Any): The audio data or path to play.
        """
        pass
