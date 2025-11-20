from abc import ABC, abstractmethod

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
