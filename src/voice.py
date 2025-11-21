"""
Voice module for Text-to-Speech generation and playback.
"""
import asyncio
import logging
import pyttsx3
import tempfile
import os
import sounddevice as sd
import soundfile as sf
import numpy as np
from src.interfaces import ITextToSpeech, IAudioPlayer
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Pyttsx3TTS(ITextToSpeech):
    """
    Offline Text-to-Speech implementation using pyttsx3.
    """
    def __init__(self, rate: int = 150, volume: float = 1.0) -> None:
        self.rate = rate
        self.volume = volume
        # We do NOT initialize the engine here anymore.
        # pyttsx3 is not thread-safe and creating the engine in the main thread
        # but using it in an executor thread causes issues (COM errors on Windows, hang on Linux).
        # We will instantiate a fresh engine inside the worker thread for each synthesis.

    async def synthesize(self, text: str) -> str:
        """
        Synthesizes text to a temporary audio file.
        
        Args:
            text (str): Text to speak.
            
        Returns:
            str: Path to the generated .wav file.
        """
        # Create a temporary file path
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            loop = asyncio.get_running_loop()
            # Run the blocking generation in a separate thread
            await loop.run_in_executor(None, self._generate_file, text, temp_path)
            return temp_path
        except Exception as e:
            logger.error(f"Error during synthesis: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return ""

    def _generate_file(self, text: str, path: str) -> None:
        """
        Blocking helper to generate audio file.
        Runs in a worker thread.
        """
        try:
            # Initialize a fresh engine instance within the thread context
            # This avoids threading issues with the COM interface on Windows
            engine = pyttsx3.init()
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            engine.save_to_file(text, path)
            engine.runAndWait()
            
            # Explicitly stop/cleanup if possible (pyttsx3 doesn't have a close/stop for instances easily)
            # but letting it go out of scope usually cleans up the COM object.
            del engine
        except Exception as e:
            logger.error(f"pyttsx3 generation error: {e}")


class ElevenLabsTTS(ITextToSpeech):
    """
    Cloud Text-to-Speech implementation using ElevenLabs API.
    """
    def __init__(self, api_key: str, voice_id: str, model_id: str = "eleven_monolingual_v1") -> None:
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        
        try:
            from elevenlabs.client import ElevenLabs
            self.client = ElevenLabs(api_key=self.api_key)
        except ImportError:
            logger.error("elevenlabs library not found. Please install it: pip install elevenlabs")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize ElevenLabs client: {e}")
            self.client = None

    async def synthesize(self, text: str) -> str:
        """
        Synthesizes text to a temporary audio file using ElevenLabs.
        """
        if not self.client:
            logger.error("ElevenLabs client not initialized. Check logs for setup errors.")
            return ""
            
        if not text or not text.strip():
            return ""

        # Create a temporary file path
        # ElevenLabs returns MP3 by default usually, but we can stream chunks.
        # We'll stick to .mp3 suffix for the temp file to be safe for playback libraries.
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_path = temp_file.name
        temp_file.close()

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._generate_file, text, temp_path)
            return temp_path
        except Exception as e:
            logger.error(f"ElevenLabs synthesis error: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return ""

    def _generate_file(self, text: str, path: str) -> None:
        """
        Blocking helper to call ElevenLabs API and save to file.
        """
        try:
            # Generate returns an iterator of bytes (stream)
            # Updated for ElevenLabs SDK 1.0+ where generate is under text_to_speech.convert
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id
            )
            
            # Write the stream to file
            # audio_stream is a generator of bytes
            with open(path, "wb") as f:
                for chunk in audio_stream:
                    if chunk:
                        f.write(chunk)
                        
        except Exception as e:
            logger.error(f"ElevenLabs API error: {e}")
            raise e


class SoundDevicePlayer(IAudioPlayer):
    """
    Plays audio using the 'sounddevice' library, supporting specific output devices.
    Useful for playing audio into a virtual cable.
    """
    def __init__(self, device_name: Optional[str] = None, device_index: Optional[int] = None, monitor: bool = True) -> None:
        """
        Initialize the player with a target device.
        
        Args:
            device_name (str, optional): Name (or partial name) of the device to use.
            device_index (int, optional): Specific index of the device to use. Takes precedence over name.
            monitor (bool): If True, plays audio to the system default device as well.
        """
        self.device_index = device_index
        self.device_name = device_name
        self.monitor = monitor
        self.target_device = self._find_device()
        
        # We re-query default device at runtime in _play_blocking usually, 
        # but getting it here is fine for logging.
        # Note: sd.default.device returns [input_idx, output_idx]
        try:
            self.default_device = sd.default.device[1]
        except Exception:
            self.default_device = None

        if self.target_device is not None:
            try:
                info = sd.query_devices(self.target_device)
                logger.info(f"Audio Player configured to use: [{self.target_device}] {info['name']}")
                if self.monitor:
                    logger.info("Audio Monitoring Enabled (System Default)")
            except Exception as e:
                logger.warning(f"Could not query device info for index {self.target_device}: {e}")
        else:
            logger.info("Audio Player configured to use: System Default")
            # If we are using system default as target, monitoring is redundant
            self.monitor = False

    def _find_device(self) -> Optional[int]:
        """
        Resolves the device index based on configuration.
        """
        # 1. Specific index provided
        if self.device_index is not None:
            return self.device_index

        # 2. Search by name
        if self.device_name:
            logger.debug(f"Searching for audio device matching: '{self.device_name}'")
            try:
                devices = sd.query_devices()
                
                # Try exact match
                for i, device in enumerate(devices):
                    if self.device_name == device['name'] and device['max_output_channels'] > 0:
                        return i
                
                # Try partial match
                for i, device in enumerate(devices):
                    if self.device_name.lower() in device['name'].lower() and device['max_output_channels'] > 0:
                        logger.info(f"Found partial match for device: '{device['name']}'")
                        return i
                
                logger.warning(f"Audio device '{self.device_name}' not found. Falling back to system default.")
            except Exception as e:
                logger.error(f"Error searching for devices: {e}")
        
        # 3. Fallback to default (None)
        return None

    async def play(self, source: Any) -> None:
        """
        Plays the audio file at the given path using sounddevice.
        """
        if not source or not isinstance(source, str) or not os.path.exists(source):
            logger.warning(f"Invalid audio source: {source}")
            return

        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, self._play_blocking, source)
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
        finally:
            # Cleanup temp file
            try:
                if os.path.exists(source):
                    os.remove(source)
            except OSError:
                pass

    def _play_blocking(self, path: str) -> None:
        """
        Blocking playback function to be run in executor.
        """
        try:
            # Ensure we read as float32 to match sounddevice defaults and avoid mismatch errors
            data, fs = sf.read(path, always_2d=True, dtype='float32')
            
            # If monitoring is enabled and we have a target device different from default
            if self.monitor and self.target_device is not None:
                try:
                    # Get current default output device dynamically
                    default_out = sd.default.device[1]
                    
                    # Chunked write is the most robust way.
                    blocksize = 1024
                    
                    # Explicitly specify dtype='float32' for streams to match data
                    with sd.OutputStream(device=self.target_device, samplerate=fs, channels=data.shape[1], blocksize=blocksize, dtype='float32') as stream1, \
                         sd.OutputStream(device=default_out, samplerate=fs, channels=data.shape[1], blocksize=blocksize, dtype='float32') as stream2:
                        
                        samples = len(data)
                        current = 0
                        while current < samples:
                            chunk = data[current:current+blocksize]
                            stream1.write(chunk)
                            stream2.write(chunk)
                            current += blocksize
                            
                except Exception as stream_err:
                    logger.error(f"Error during dual playback: {stream_err}")
                    # Fallback: just play to target
                    sd.play(data, fs, device=self.target_device, blocking=True)
                    sd.stop()
            else:
                # Standard single device playback
                sd.play(data, fs, device=self.target_device, blocking=True)
                sd.stop()
                
        except Exception as e:
            logger.error(f"Playback failed: {e}")
