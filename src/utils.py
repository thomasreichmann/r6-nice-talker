import time
import logging
import functools
import re

logger = logging.getLogger(__name__)


def measure_latency(description: str = None):
    """
    Decorator to measure and log the execution time of a function.
    
    Args:
        description (str): Custom description for the log. If None, uses function name.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # We use finally to ensure we log even if the function raises an exception
                end_time = time.time()
                latency = end_time - start_time
                
                name = description or func.__name__
                logger.info(f"[Latency] {name}: {latency:.4f}s")
        return wrapper
    return decorator


def remove_emojis(text: str) -> str:
    """
    Removes emojis and other non-BMP characters from a string.
    
    Args:
        text (str): The string to remove emojis from.
        
    Returns:
        str: The cleaned string with emojis removed.
    """
    # Matches standard emoji unicode ranges
    # This regex handles most common emojis
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # Emoticons
        u"\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
        u"\U0001F680-\U0001F6FF"  # Transport and Map
        u"\U0001F1E0-\U0001F1FF"  # Flags (iOS)
        u"\U00002700-\U000027BF"  # Dingbats
        u"\U00002600-\U000026FF"  # Misc symbols
        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "]+", flags=re.UNICODE)
    
    return emoji_pattern.sub(r'', text).strip()

