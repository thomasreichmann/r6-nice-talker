from src.interfaces import IMessageProvider, ISwitchableMessageProvider
from src.config import Config
from src.utils import measure_latency, remove_emojis
from src.context import get_random_context
from src.constants import USER_PROMPT_TEMPLATES, get_system_prompt
from src.sounds import SoundManager
from src.cache import get_cache
import random
import json
import logging
import threading
import time
from collections import deque
from openai import AsyncOpenAI
from pathlib import Path

logger = logging.getLogger(__name__)

# Optional: watchdog for hot-reload
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    logger.debug("watchdog not installed, hot-reload disabled")

class FixedMessageProvider(IMessageProvider):
    """
    A simple message provider that always returns the same fixed string.
    Useful for testing or sending the same message repeatedly.
    
    Args:
        message (str): The fixed message to always return.
    """
    def __init__(self, message: str) -> None:
        self.message = message

    async def get_message(self, mode: str = "text", context_override: str = None) -> str:
        return self.message


class RandomMessageProvider(IMessageProvider):
    """
    Returns a random message from a predefined list.
    Useful for adding variety without AI generation.
    
    Args:
        messages (list[str]): List of possible messages to choose from.
    """
    def __init__(self, messages: list[str]) -> None:
        self.messages = messages

    async def get_message(self, mode: str = "text", context_override: str = None) -> str:
        if not self.messages:
            return ""
        return random.choice(self.messages)

class PromptsFileWatcher(FileSystemEventHandler):
    """Watches prompts.json for changes and triggers reload."""
    
    def __init__(self, provider, event_bus=None):
        self.provider = provider
        self.event_bus = event_bus
        self.prompts_file = Path(provider.prompts_file).resolve()
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Check if the modified file is our prompts file
        modified_path = Path(event.src_path).resolve()
        if modified_path == self.prompts_file:
            logger.info("prompts.json modified, reloading...")
            self.provider.reload_prompts()
            
            # Emit event if event_bus available
            if self.event_bus:
                from src.events import Event, EventType
                self.event_bus.publish(Event(EventType.PROMPTS_RELOADED))


class ChatGPTProvider(ISwitchableMessageProvider):
    """
    Generates messages using OpenAI's ChatGPT API based on selectable personas.
    Loads personas from prompts.json and uses the BASE_SYSTEM_PROMPT for all interactions.
    
    Args:
        api_key (str): OpenAI API key for authentication.
        model (str): The OpenAI model to use (defaults to gpt-3.5-turbo).
        prompts_file (str): Path to JSON file containing persona definitions.
        event_bus: Optional EventBus for hot-reload notifications.
    """
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", prompts_file: str = "prompts.json", event_bus=None):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.prompts_file = prompts_file
        self.prompts = self._load_prompts(prompts_file)
        self.current_index = 0
        self.event_bus = event_bus
        self.file_observer = None
        
        # User templates are static, system prompts are dynamic now
        self.user_prompt_template = USER_PROMPT_TEMPLATES.get(Config.LANGUAGE, USER_PROMPT_TEMPLATES["en"])
        
        # Store the last 5 generated messages to maintain context/style consistency
        self.history = deque(maxlen=5)
        
        if not self.prompts:
            # Fallback if file is empty or missing
            self.prompts = [{"name": "Default", "prompt": "Style: Helpful teammate."}]
        else:
             # Try to find "Toxic" and set it as default
             for i, p in enumerate(self.prompts):
                 if p["name"] == "Toxic":
                     self.current_index = i
                     break
            
        logger.info(f"ChatGPTProvider initialized with {len(self.prompts)} personas.")
        logger.info(f"Current Persona: {self.get_current_mode_name()}")
        
        # Setup hot-reload if enabled
        if Config.PROMPTS_HOT_RELOAD and HAS_WATCHDOG:
            self._setup_hot_reload()
    
    def _setup_hot_reload(self):
        """Setup file watcher for prompts.json hot-reload."""
        try:
            prompts_path = Path(self.prompts_file).resolve()
            watch_dir = prompts_path.parent
            
            event_handler = PromptsFileWatcher(self, self.event_bus)
            self.file_observer = Observer()
            self.file_observer.schedule(event_handler, str(watch_dir), recursive=False)
            self.file_observer.start()
            
            logger.info(f"Hot-reload enabled for {self.prompts_file}")
        except Exception as e:
            logger.warning(f"Could not setup hot-reload: {e}")
    
    def reload_prompts(self):
        """Reload prompts from file (called by file watcher)."""
        try:
            old_persona_name = self.get_current_mode_name()
            new_prompts = self._load_prompts(self.prompts_file)
            
            if not new_prompts:
                logger.error("Reload failed: prompts file is empty or invalid")
                return
            
            self.prompts = new_prompts
            
            # Try to keep the same persona if it still exists
            found = False
            for i, p in enumerate(self.prompts):
                if p["name"] == old_persona_name:
                    self.current_index = i
                    found = True
                    break
            
            if not found:
                self.current_index = 0
                logger.warning(f"Previous persona '{old_persona_name}' not found, reset to first")
            
            # Clear history on reload
            self.history.clear()
            
            logger.info(f"✓ Prompts reloaded ({len(self.prompts)} personas)")
            logger.info(f"Current Persona: {self.get_current_mode_name()}")
            
            # Play sound feedback
            SoundManager.play_success()
            
        except Exception as e:
            logger.error(f"Error reloading prompts: {e}")
            SoundManager.play_error()
    def _load_prompts(self, filepath: str) -> list[dict]:
        """
        Loads persona definitions from a JSON file and resolves the prompt for the current language.
        
        Args:
            filepath (str): Path to the prompts JSON file.
            
        Returns:
            list[dict]: List of persona dictionaries with 'name' and 'prompt' keys.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                if not isinstance(data, list):
                    logger.error("prompts.json must be a list of personas.")
                    return []
                
                language = Config.LANGUAGE
                resolved_personas = []
                
                for persona in data:
                    # Handle legacy format (where 'prompt' is a string)
                    if isinstance(persona.get('prompts'), str) or 'prompt' in persona:
                        # If using old key 'prompt' or simple string, treat as English default
                        raw_prompt = persona.get('prompt', persona.get('prompts', ''))
                        if language == 'en':
                             resolved_personas.append({
                                 "name": persona["name"],
                                 "prompt": raw_prompt
                             })
                        continue

                    # Handle new format (where 'prompts' is a dict)
                    prompts_dict = persona.get('prompts', {})
                    if isinstance(prompts_dict, dict):
                        # Get prompt for config language, fallback to English
                        prompt_text = prompts_dict.get(language)
                        if not prompt_text:
                             prompt_text = prompts_dict.get('en', "")
                             
                        if prompt_text:
                            resolved_personas.append({
                                "name": persona["name"],
                                "prompt": prompt_text
                            })
                
                return resolved_personas
                
        except Exception as e:
            logger.error(f"Failed to load prompts from {filepath}: {e}")
            return []

    @measure_latency(description="ChatGPT Generation")
    async def get_message(self, mode: str = "text", context_override: str = None) -> str:
        """
        Generates a chat message using the current persona and a random game context.
        
        Args:
            mode (str): 'text' for short chat messages, 'voice' for spoken lines.
            context_override (str): Optional specific context to use instead of random.
        
        Returns:
            str: Generated chat message suitable for in-game use.
        """
        current_persona = self.prompts[self.current_index]
        style_prompt = current_persona["prompt"]
        
        has_vision = False
        if context_override:
            context_scenario = context_override
            has_vision = True
        else:
            context_scenario = get_random_context(Config.LANGUAGE)
        
        # Check cache first
        cache = get_cache()
        cached_message = cache.get(
            persona_name=current_persona["name"],
            context=context_scenario,
            mode=mode,
            language=Config.LANGUAGE
        )
        
        if cached_message:
            logger.info(f"Using cached message for {current_persona['name']}")
            return cached_message
        
        # DRY-RUN mode: return mock response
        if Config.DRY_RUN:
            mock_message = f"[DRY-RUN] Mock message from {current_persona['name']}"
            logger.info(f"[DRY-RUN] Would call OpenAI with persona={current_persona['name']}, context={context_scenario}, mode={mode}")
            return mock_message
        
        logger.info(f"Generating ({mode}) message with persona: {current_persona['name']} | Context: {context_scenario}")
        
        # Dynamically construct system prompt
        base_system_prompt = get_system_prompt(Config.LANGUAGE, mode, has_vision=has_vision)
        
        # Select user prompt template
        lang_templates = USER_PROMPT_TEMPLATES.get(Config.LANGUAGE, USER_PROMPT_TEMPLATES["en"])
        user_prompt_template = lang_templates.get(mode, lang_templates.get("text"))

        # Construct a dynamic prompt using the centralized base prompt
        final_system_prompt = f"{base_system_prompt}\n\nPersona/Style: {style_prompt}"
        # Formatter template with the scenario
        user_prompt = user_prompt_template.format(scenario=context_scenario)
        
        # Build message list with history
        messages = [{"role": "system", "content": final_system_prompt}]
        
        # Add history (previous things we said)
        for past_msg in self.history:
            messages.append({"role": "assistant", "content": past_msg})
            
        # Add current prompt
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            # Adjust max_tokens for voice to allow longer responses
            max_tokens = 90 if mode == "text" else 130
            
            start_time = time.time()
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens, 
                temperature=1.0, # High temperature for creativity
                frequency_penalty=0.6 # Stronger penalty to prevent repetition
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            # Track analytics
            if hasattr(response, 'usage') and response.usage:
                try:
                    from src.analytics import get_analytics
                    analytics = get_analytics()
                    analytics.track_api_call(
                        provider="openai",
                        model=self.model,
                        tokens_input=response.usage.prompt_tokens,
                        tokens_output=response.usage.completion_tokens,
                        latency_ms=elapsed_ms
                    )
                except Exception as e:
                    logger.debug(f"Analytics tracking failed: {e}")
            
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
            
            # Cache the result
            cache.set(
                content,
                persona_name=current_persona["name"],
                context=context_scenario,
                mode=mode,
                language=Config.LANGUAGE
            )
            
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
