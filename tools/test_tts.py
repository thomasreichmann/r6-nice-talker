"""
Standalone TTS Testing Tool
Test Text-to-Speech engines without running the bot.
"""
import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.voice import Pyttsx3TTS, ElevenLabsTTS, SoundDevicePlayer
from src.config import Config
from src.logging_config import setup_logging
import logging

logger = logging.getLogger(__name__)


async def test_tts(
    provider: str,
    text: str,
    save_output: bool = False,
    play_audio: bool = True,
    voice_id: str = None,
    rate: int = 150
) -> None:
    """
    Test a TTS engine with custom text.
    
    Args:
        provider: TTS provider to use ('pyttsx3' or 'elevenlabs')
        text: Text to synthesize
        save_output: Save the audio file instead of deleting
        play_audio: Play the audio after generation
        voice_id: ElevenLabs voice ID (if using elevenlabs)
        rate: Speech rate for pyttsx3
    """
    logger.info(f"Testing {provider.upper()} TTS...")
    logger.info(f"Text: '{text}'")
    
    # Initialize TTS engine
    if provider == "pyttsx3":
        tts = Pyttsx3TTS(rate=rate)
        logger.info(f"Using pyttsx3 with rate={rate}")
    elif provider == "elevenlabs":
        api_key = Config.ELEVENLABS_API_KEY
        if not api_key:
            logger.error("ELEVENLABS_API_KEY not set in .env file")
            return
        
        voice = voice_id or Config.ELEVENLABS_VOICE_ID
        tts = ElevenLabsTTS(
            api_key=api_key,
            voice_id=voice,
            model_id=Config.ELEVENLABS_MODEL_ID,
            stability=Config.ELEVENLABS_STABILITY,
            similarity_boost=Config.ELEVENLABS_SIMILARITY_BOOST
        )
        logger.info(f"Using ElevenLabs with voice_id={voice}")
    else:
        logger.error(f"Unknown provider: {provider}")
        return
    
    # Synthesize
    logger.info("Synthesizing audio...")
    try:
        audio_path = await tts.synthesize(text)
        
        if not audio_path:
            logger.error("Synthesis failed - no audio file generated")
            return
        
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return
        
        file_size = os.path.getsize(audio_path)
        logger.info(f"✓ Audio generated: {audio_path} ({file_size} bytes)")
        
        # Play audio if requested
        if play_audio:
            logger.info("Playing audio...")
            player = SoundDevicePlayer(
                device_name=Config.AUDIO_OUTPUT_DEVICE_NAME,
                device_index=Config.AUDIO_OUTPUT_DEVICE_INDEX,
                monitor=Config.AUDIO_MONITORING
            )
            
            # Temporarily save the path to prevent deletion
            temp_path = audio_path
            if save_output:
                import shutil
                save_path = f"tts_output_{provider}.{'mp3' if provider == 'elevenlabs' else 'wav'}"
                shutil.copy(audio_path, save_path)
                logger.info(f"✓ Saved to: {save_path}")
                
            await player.play(temp_path)
            logger.info("✓ Playback complete")
        else:
            # If not playing, handle the temp file
            if save_output:
                import shutil
                save_path = f"tts_output_{provider}.{'mp3' if provider == 'elevenlabs' else 'wav'}"
                shutil.move(audio_path, save_path)
                logger.info(f"✓ Saved to: {save_path}")
            else:
                # Clean up temp file
                try:
                    os.remove(audio_path)
                except:
                    pass
                    
    except Exception as e:
        logger.error(f"Error during synthesis: {e}", exc_info=True)
        return


def main():
    parser = argparse.ArgumentParser(
        description="Test TTS engines without running the bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/test_tts.py --text "Hello world" --provider pyttsx3
  python tools/test_tts.py --text "Testing voice" --provider elevenlabs --save
  python tools/test_tts.py --provider pyttsx3 --rate 200 --no-play --save
        """
    )
    
    parser.add_argument(
        "--provider",
        choices=["pyttsx3", "elevenlabs"],
        default="pyttsx3",
        help="TTS provider to use (default: pyttsx3)"
    )
    
    parser.add_argument(
        "--text",
        type=str,
        help="Text to synthesize (if not provided, prompts interactively)"
    )
    
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the generated audio file"
    )
    
    parser.add_argument(
        "--no-play",
        action="store_true",
        help="Skip audio playback"
    )
    
    parser.add_argument(
        "--voice-id",
        type=str,
        help="ElevenLabs voice ID (only for elevenlabs provider)"
    )
    
    parser.add_argument(
        "--rate",
        type=int,
        default=150,
        help="Speech rate for pyttsx3 (default: 150)"
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
        print("\nEnter text to synthesize (or 'quit' to exit):")
        text = input("> ").strip()
        if text.lower() in ['quit', 'exit', 'q']:
            print("Exiting...")
            return
        if not text:
            print("No text provided. Exiting...")
            return
    
    # Run test
    try:
        asyncio.run(test_tts(
            provider=args.provider,
            text=text,
            save_output=args.save,
            play_audio=not args.no_play,
            voice_id=args.voice_id,
            rate=args.rate
        ))
        logger.info("Test complete!")
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()

