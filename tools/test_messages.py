"""
Standalone Message Generation Testing Tool
Test message generation without running the bot or wasting API calls.
"""
import asyncio
import argparse
import sys
import json
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.providers import ChatGPTProvider
from src.config import Config
from src.context import get_random_context
from src.logging_config import setup_logging
import logging

logger = logging.getLogger(__name__)


async def test_message_generation(
    persona: str = None,
    context: str = None,
    mode: str = "text",
    dry_run: bool = False,
    show_tokens: bool = True
) -> None:
    """
    Test message generation with a specific persona and context.
    
    Args:
        persona: Persona name to use (or None for current)
        context: Custom context (or None for random)
        mode: Generation mode ('text' or 'voice')
        dry_run: If True, show what would be sent without calling API
        show_tokens: Display token usage and cost estimate
    """
    # Check API key
    if not Config.OPENAI_API_KEY and not dry_run:
        logger.error("OPENAI_API_KEY not set in .env file")
        logger.info("Use --dry-run to test without API calls")
        return
    
    # Initialize provider
    logger.info("Initializing ChatGPT provider...")
    provider = ChatGPTProvider(
        api_key=Config.OPENAI_API_KEY,
        model=Config.OPENAI_MODEL
    )
    
    # Switch to requested persona if specified
    if persona:
        # Find persona by name
        found = False
        for i, p in enumerate(provider.prompts):
            if p["name"].lower() == persona.lower():
                provider.current_index = i
                found = True
                break
        
        if not found:
            logger.error(f"Persona '{persona}' not found")
            logger.info(f"Available personas: {', '.join([p['name'] for p in provider.prompts])}")
            return
    
    current_persona = provider.prompts[provider.current_index]
    logger.info(f"Using persona: {current_persona['name']}")
    
    # Get or generate context
    if not context:
        context = get_random_context(Config.LANGUAGE)
    
    logger.info(f"Context: {context}")
    logger.info(f"Mode: {mode}")
    logger.info("-" * 60)
    
    if dry_run:
        # Show what would be sent without making API call
        from src.constants import get_system_prompt, USER_PROMPT_TEMPLATES
        
        base_system_prompt = get_system_prompt(Config.LANGUAGE, mode, has_vision=False)
        style_prompt = current_persona["prompt"]
        final_system_prompt = f"{base_system_prompt}\n\nPersona/Style: {style_prompt}"
        
        lang_templates = USER_PROMPT_TEMPLATES.get(Config.LANGUAGE, USER_PROMPT_TEMPLATES["en"])
        user_prompt_template = lang_templates.get(mode, lang_templates.get("text"))
        user_prompt = user_prompt_template.format(scenario=context)
        
        logger.info("[DRY-RUN] Would send to OpenAI:")
        logger.info(f"Model: {Config.OPENAI_MODEL}")
        logger.info(f"System Prompt: {final_system_prompt[:200]}...")
        logger.info(f"User Prompt: {user_prompt}")
        logger.info("[DRY-RUN] No actual API call made")
    else:
        # Actually generate message
        logger.info("Generating message...")
        start_time = time.time()
        
        try:
            message = await provider.get_message(mode=mode, context_override=context)
            
            elapsed = time.time() - start_time
            logger.info("-" * 60)
            logger.info(f"✓ Generated in {elapsed:.2f}s")
            logger.info(f"Message: '{message}'")
            logger.info(f"Length: {len(message)} characters")
            
            if show_tokens:
                # Estimate token count (rough approximation: 1 token ≈ 4 chars)
                estimated_tokens = len(message) // 4
                logger.info(f"Estimated tokens: ~{estimated_tokens}")
                
                # Estimate cost (very rough)
                # For gpt-4o-mini: input ~$0.00015/1k, output ~$0.0006/1k
                estimated_cost = (estimated_tokens / 1000.0) * Config.OPENAI_COST_PER_1K_TOKENS_OUTPUT
                logger.info(f"Estimated cost: ~${estimated_cost:.6f}")
                
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)


def main():
    parser = argparse.ArgumentParser(
        description="Test message generation without running the bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/test_messages.py --persona Toxic --context "We just won 5-4"
  python tools/test_messages.py --list-personas
  python tools/test_messages.py --mode voice --dry-run
  python tools/test_messages.py --persona Wholesome --random-context
        """
    )
    
    parser.add_argument(
        "--persona",
        type=str,
        help="Persona name to use"
    )
    
    parser.add_argument(
        "--context",
        type=str,
        help="Custom context to use"
    )
    
    parser.add_argument(
        "--random-context",
        action="store_true",
        help="Use a random context from the context pool"
    )
    
    parser.add_argument(
        "--mode",
        choices=["text", "voice"],
        default="text",
        help="Generation mode (default: text)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be sent without calling API"
    )
    
    parser.add_argument(
        "--list-personas",
        action="store_true",
        help="List all available personas and exit"
    )
    
    parser.add_argument(
        "--no-tokens",
        action="store_true",
        help="Don't show token usage estimates"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    # List personas if requested
    if args.list_personas:
        try:
            with open("prompts.json", "r", encoding="utf-8") as f:
                prompts = json.load(f)
            
            print("\nAvailable Personas:")
            print("-" * 60)
            for i, persona in enumerate(prompts, 1):
                name = persona.get("name", "Unknown")
                prompts_dict = persona.get("prompts", {})
                if isinstance(prompts_dict, dict):
                    prompt = prompts_dict.get(Config.LANGUAGE, prompts_dict.get("en", ""))
                else:
                    prompt = str(prompts_dict)
                
                preview = prompt[:80] + "..." if len(prompt) > 80 else prompt
                print(f"{i}. {name}")
                print(f"   {preview}")
                print()
        except Exception as e:
            logger.error(f"Could not load personas: {e}")
        return
    
    # Determine context
    context = None
    if args.context:
        context = args.context
    elif args.random_context:
        context = None  # Will be generated
    else:
        # Prompt for context
        print("\nEnter custom context (or press Enter for random):")
        user_input = input("> ").strip()
        if user_input:
            context = user_input
    
    # Run test
    try:
        asyncio.run(test_message_generation(
            persona=args.persona,
            context=context,
            mode=args.mode,
            dry_run=args.dry_run,
            show_tokens=not args.no_tokens
        ))
        logger.info("Test complete!")
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()

