"""
Standalone Typer Testing Tool
Test chat typing behavior without running the bot.
"""
import asyncio
import argparse
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.typers import R6SiegeTyper, DebugTyper
from src.config import Config
from src.logging_config import setup_logging
import logging

logger = logging.getLogger(__name__)


async def test_typer(
    text: str,
    typer_type: str = "r6",
    open_chat_delay: float = None,
    typing_interval: float = None,
    dry_run: bool = False,
    repeat: int = 1,
    measure_timing: bool = True
) -> None:
    """
    Test chat typing with configurable parameters.
    
    Args:
        text: Text to type
        typer_type: Typer to use ('r6' or 'debug')
        open_chat_delay: Delay after opening chat (seconds)
        typing_interval: Delay between keystrokes (seconds)
        dry_run: If True, use DebugTyper regardless of typer_type
        repeat: Number of times to repeat the typing
        measure_timing: Measure and report timing consistency
    """
    # Use defaults from config if not specified
    if open_chat_delay is None:
        open_chat_delay = Config.OPEN_CHAT_DELAY
    if typing_interval is None:
        typing_interval = Config.TYPING_INTERVAL
    
    logger.info(f"Testing {'DebugTyper' if dry_run else typer_type.upper()} typer")
    logger.info(f"Text: '{text}' ({len(text)} chars)")
    logger.info(f"Open chat delay: {open_chat_delay}s")
    logger.info(f"Typing interval: {typing_interval}s")
    
    # Calculate expected time
    expected_time = open_chat_delay + (len(text) * typing_interval) + 0.1  # +0.1 for final delay
    logger.info(f"Expected duration: ~{expected_time:.2f}s")
    logger.info("-" * 60)
    
    # Initialize typer
    if dry_run or typer_type == "debug":
        typer = DebugTyper()
    else:
        typer = R6SiegeTyper(
            open_chat_delay=open_chat_delay,
            typing_interval=typing_interval
        )
    
    # Perform typing test(s)
    timings = []
    
    for i in range(repeat):
        if repeat > 1:
            logger.info(f"\nAttempt {i+1}/{repeat}")
        
        if not dry_run and i > 0:
            # Wait between attempts to allow game to be ready
            logger.info("Waiting 3s before next attempt...")
            await asyncio.sleep(3)
        
        try:
            start_time = time.time()
            await typer.send(text)
            elapsed = time.time() - start_time
            
            timings.append(elapsed)
            
            if measure_timing:
                logger.info(f"✓ Completed in {elapsed:.3f}s")
                deviation = abs(elapsed - expected_time)
                logger.info(f"  Deviation from expected: {deviation:.3f}s ({(deviation/expected_time)*100:.1f}%)")
                
        except Exception as e:
            logger.error(f"✗ Typing failed: {e}", exc_info=True)
    
    # Report timing statistics if multiple attempts
    if len(timings) > 1:
        logger.info("\n" + "=" * 60)
        logger.info("Timing Statistics:")
        logger.info(f"  Attempts: {len(timings)}")
        logger.info(f"  Min: {min(timings):.3f}s")
        logger.info(f"  Max: {max(timings):.3f}s")
        logger.info(f"  Mean: {sum(timings)/len(timings):.3f}s")
        
        # Calculate standard deviation
        mean = sum(timings) / len(timings)
        variance = sum((x - mean) ** 2 for x in timings) / len(timings)
        std_dev = variance ** 0.5
        logger.info(f"  Std Dev: {std_dev:.3f}s")
    
    logger.info("\n" + "=" * 60)
    logger.info("Typer test complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Test chat typing behavior without running the bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/test_typer.py --text "test" --interval 0.01 --dry-run
  python tools/test_typer.py --text "Hello team!" --repeat 5
  python tools/test_typer.py --typer debug --text "Testing..."
  python tools/test_typer.py --text "gl hf" --delay 0.5 --interval 0.02
        """
    )
    
    parser.add_argument(
        "--text",
        type=str,
        help="Text to type (if not provided, prompts interactively)"
    )
    
    parser.add_argument(
        "--typer",
        choices=["r6", "debug"],
        default="r6",
        help="Typer to use (default: r6)"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        help="Open chat delay in seconds (default: from config)"
    )
    
    parser.add_argument(
        "--interval",
        type=float,
        help="Typing interval in seconds (default: from config)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use DebugTyper (just log, don't actually type)"
    )
    
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of times to repeat the test (default: 1)"
    )
    
    parser.add_argument(
        "--no-timing",
        action="store_true",
        help="Don't measure timing consistency"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    # Get text interactively if not provided
    text = args.text
    if not text:
        print("\nEnter text to type (or 'quit' to exit):")
        text = input("> ").strip()
        if text.lower() in ['quit', 'exit', 'q']:
            print("Exiting...")
            return
        if not text:
            print("No text provided. Exiting...")
            return
    
    # Warning for non-dry-run
    if not args.dry_run and args.typer == "r6":
        print("\n⚠ WARNING: This will actually type in your game!")
        print("Make sure the game is focused and you're ready.")
        print("Press Enter to continue or Ctrl+C to cancel...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nCancelled.")
            return
    
    # Run test
    try:
        asyncio.run(test_typer(
            text=text,
            typer_type=args.typer,
            open_chat_delay=args.delay,
            typing_interval=args.interval,
            dry_run=args.dry_run,
            repeat=args.repeat,
            measure_timing=not args.no_timing
        ))
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()

