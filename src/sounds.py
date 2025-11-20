import winsound
import threading
import logging

logger = logging.getLogger(__name__)

class SoundManager:
    """
    Manages audio feedback for the application using Windows system beeps.
    Runs beeps in a separate thread to avoid blocking the main execution.
    """
    
    @staticmethod
    def _beep(frequency, duration):
        try:
            winsound.Beep(frequency, duration)
        except Exception as e:
            logger.warning(f"Failed to play sound: {e}")

    @classmethod
    def play_async(cls, frequency, duration):
        threading.Thread(target=cls._beep, args=(frequency, duration), daemon=True).start()

    @classmethod
    def play_success(cls):
        """High pitched short beep for successful triggers."""
        cls.play_async(1000, 150)

    @classmethod
    def play_error(cls):
        """Low pitched long beep for errors."""
        cls.play_async(400, 500)

    @classmethod
    def play_mode_switch(cls):
        """Deprecated: Generic switch sound."""
        def sequence():
            try:
                winsound.Beep(600, 100)
                winsound.Beep(800, 100)
            except Exception:
                pass
        threading.Thread(target=sequence, daemon=True).start()

    @classmethod
    def play_persona_switch(cls, index: int):
        """
        Plays a unique tone based on the persona index.
        Base frequency 400Hz, increases by 150Hz per index.
        """
        frequency = 400 + (index * 150)
        # Cap frequency at 3000Hz to prevent ear bleeding
        frequency = min(frequency, 3000)
        cls.play_async(frequency, 200)
