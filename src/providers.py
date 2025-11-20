from src.interfaces import IMessageProvider, ISwitchableMessageProvider
from src.config import Config
from src.utils import measure_latency, remove_emojis
from src.context import get_random_context
from src.sounds import SoundManager
import random
import json
import logging
from collections import deque
from openai import OpenAI

logger = logging.getLogger(__name__)

class FixedMessageProvider(IMessageProvider):
    """
    Always returns the same fixed string.
    """
    def __init__(self, message: str):
        self.message = message

    def get_message(self) -> str:
        return self.message

class RandomMessageProvider(IMessageProvider):
    """
    Returns a random message from a list.
    """
    def __init__(self, messages: list[str]):
        self.messages = messages

    def get_message(self) -> str:
        if not self.messages:
            return ""
        return random.choice(self.messages)

class ChatGPTProvider(ISwitchableMessageProvider):
    """
    Generates messages using OpenAI's ChatGPT API based on selectable personas.
    Loads personas from prompts.json.
    """
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", prompts_file: str = "prompts.json"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.prompts = self._load_prompts(prompts_file)
        self.current_index = 0
        
        # Store the last 5 generated messages to maintain context/style consistency
        self.history = deque(maxlen=5)
        
        # Global instructions that apply to ALL personas
        self.base_instructions = (
            "You are a player in a Rainbow Six Siege match. "
            "Write a single, short in-game chat message (under 120 chars). "
            "Adopt the vernacular of a digital native gamer (informal, rapid-fire, low-effort typing). "
            "Use text-based emoticons if needed, but never emojis. "
            "Write like a stream of consciousness or Twitch chat. Avoid punctuation and uppercase letters unless for emphasis. "
            "Never use formal greetings like 'Hey team' or 'Hello'. "
            "Your response must strictly follow the style of the assigned Persona."
        )
        
        if not self.prompts:
            # Fallback if file is empty or missing
            self.prompts = [{"name": "Default", "prompt": "Style: Helpful teammate."}]
        else:
             # Try to find "Reputation Farmer" and set it as default
             for i, p in enumerate(self.prompts):
                 if p["name"] == "Reputation Farmer":
                     self.current_index = i
                     break
            
        logger.info(f"ChatGPTProvider initialized with {len(self.prompts)} personas.")
        logger.info(f"Current Persona: {self.get_current_mode_name()}")
    def _load_prompts(self, filepath: str) -> list[dict]:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data
        except Exception as e:
            logger.error(f"Failed to load prompts from {filepath}: {e}")
            return []

    @measure_latency(description="ChatGPT Generation")
    def get_message(self) -> str:
        current_persona = self.prompts[self.current_index]
        style_prompt = current_persona["prompt"]
        context_scenario = get_random_context()
        
        logger.info(f"Generating message with persona: {current_persona['name']} | Context: {context_scenario}")
        
        # Construct a dynamic prompt
        final_system_prompt = f"{self.base_instructions}\n\nPersona/Style: {style_prompt}"
        user_prompt = f"Current Match Situation: {context_scenario}\nWrite a chat message reacting to this situation."
        
        # Build message list with history
        messages = [{"role": "system", "content": final_system_prompt}]
        
        # Add history (previous things we said)
        for past_msg in self.history:
            messages.append({"role": "assistant", "content": past_msg})
            
        # Add current prompt
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=60, # Keep it short for chat limits
                temperature=1.0, # High temperature for creativity
                frequency_penalty=0.6 # Stronger penalty to prevent repetition
            )
            content = response.choices[0].message.content.strip()
            
            # Cleanup quotes if the model adds them
            content = content.replace('"', '').replace("'", "")

            # Strip Hashtags (AI loves adding #RainbowSixSiege)
            if '#' in content:
                content = content.split('#')[0].strip()
                
            # Strip Emojis (Games can't display them)
            content = remove_emojis(content)
            
            # Add to history
            self.history.append(content)
            
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}")
            SoundManager.play_error()
            content = "Error generating message."
            
        logger.info(f"Generated content: {content}")
        return content

    def next_mode(self) -> None:
        self.current_index = (self.current_index + 1) % len(self.prompts)
        self.history.clear()
        logger.info(f"Switched to Persona: {self.get_current_mode_name()}")
        SoundManager.play_persona_switch(self.current_index)

    def prev_mode(self) -> None:
        self.current_index = (self.current_index - 1) % len(self.prompts)
        self.history.clear()
        logger.info(f"Switched to Persona: {self.get_current_mode_name()}")
        SoundManager.play_persona_switch(self.current_index)

    def get_current_mode_name(self) -> str:
        return self.prompts[self.current_index]["name"]
