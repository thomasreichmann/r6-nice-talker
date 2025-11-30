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
        # DRY-RUN mode: skip synthesis
        from src.config import Config
        if Config.DRY_RUN:
            logger.info(f"[DRY-RUN] Would synthesize with pyttsx3: '{text}'")
            return "[DRY-RUN-AUDIO]"
        
        # Create a temporary file path
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            loop = asyncio.get_running_loop()
            # Run the blocking generation in a separate thread
            import time
            start_time = time.time()
            await loop.run_in_executor(None, self._generate_file, text, temp_path)
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            # Track analytics
            try:
                from src.analytics import get_analytics
                analytics = get_analytics()
                analytics.track_tts(
                    provider="pyttsx3",
                    char_count=len(text),
                    latency_ms=elapsed_ms
                )
            except Exception as e:
                logger.debug(f"Analytics tracking failed: {e}")
            
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
    def __init__(self, api_key: str, voice_id: str, model_id: str = "eleven_monolingual_v1", stability: float = 0.5, similarity_boost: float = 0.75) -> None:
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.stability = stability
        self.similarity_boost = similarity_boost
        
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
        # DRY-RUN mode: skip synthesis
        from src.config import Config
        if Config.DRY_RUN:
            logger.info(f"[DRY-RUN] Would synthesize with ElevenLabs: '{text}' (voice_id={self.voice_id})")
            return "[DRY-RUN-AUDIO]"
        
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
            import time
            start_time = time.time()
            await loop.run_in_executor(None, self._generate_file, text, temp_path)
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            # Track analytics
            try:
                from src.analytics import get_analytics
                analytics = get_analytics()
                analytics.track_tts(
                    provider="elevenlabs",
                    char_count=len(text),
                    latency_ms=elapsed_ms
                )
            except Exception as e:
                logger.debug(f"Analytics tracking failed: {e}")
            
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
            
            # Construct voice settings if library supports it via dict or object
            # Check elevenlabs structure for VoiceSettings
            from elevenlabs import VoiceSettings
            
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id,
                voice_settings=VoiceSettings(
                    stability=self.stability,
                    similarity_boost=self.similarity_boost
                )
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
    def __init__(self, device_name: Optional[str] = None, device_index: Optional[int] = None, monitor: bool = True, preferred_driver: Optional[str] = None) -> None:
        """
        Initialize the player with a target device.
        
        Args:
            device_name (str, optional): Name (or partial name) of the device to use.
            device_index (int, optional): Specific index of the device to use. Takes precedence over name.
            monitor (bool): If True, plays audio to the system default device as well.
            preferred_driver (str, optional): Preferred audio driver/API (e.g., "WASAPI", "DirectSound", "ASIO").
                                             If set, will attempt to find device in this driver first, then fallback to others.
        """
        self.device_index = device_index
        self.device_name = device_name
        self.monitor = monitor
        self.preferred_driver = preferred_driver
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
                host_api_name = sd.query_hostapis(info['hostapi'])['name']
                api_status = "MME" if host_api_name == "MME" else f"non-MME ({host_api_name})"
                logger.info(f"Audio Player configured to use: [{self.target_device}] {info['name']} (API: {api_status})")
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
        If preferred_driver is set, attempts to find device in that driver first,
        then falls back to other drivers. Otherwise, prefers non-MME devices.
        """
        # 1. Specific index provided
        if self.device_index is not None:
            return self.device_index

        # 2. Search by name
        if self.device_name:
            logger.debug(f"Searching for audio device matching: '{self.device_name}'")
            if self.preferred_driver:
                logger.debug(f"Preferred driver: '{self.preferred_driver}'")
            try:
                devices = sd.query_devices()
                host_apis = sd.query_hostapis()
                
                # Helper function to get API name for a device
                def get_api_name(device):
                    try:
                        return host_apis[device['hostapi']]['name']
                    except (KeyError, IndexError):
                        return None
                
                # Helper function to check if device uses a specific API
                def is_api_device(device, api_name):
                    return get_api_name(device) == api_name
                
                # Helper function to check if device uses MME API
                def is_mme_device(device):
                    return is_api_device(device, "MME")
                
                # If preferred driver is set, try to find device in that driver first
                if self.preferred_driver:
                    preferred_driver_upper = self.preferred_driver.upper()
                    
                    # Try exact match in preferred driver
                    for i, device in enumerate(devices):
                        if (self.device_name == device['name'] and 
                            device['max_output_channels'] > 0 and
                            is_api_device(device, preferred_driver_upper)):
                            logger.info(f"Found exact match in preferred driver '{preferred_driver_upper}': '{device['name']}'")
                            return i
                    
                    # Try partial match in preferred driver
                    for i, device in enumerate(devices):
                        if (self.device_name.lower() in device['name'].lower() and 
                            device['max_output_channels'] > 0 and
                            is_api_device(device, preferred_driver_upper)):
                            logger.info(f"Found partial match in preferred driver '{preferred_driver_upper}': '{device['name']}'")
                            return i
                    
                    logger.info(f"Device '{self.device_name}' not found in preferred driver '{preferred_driver_upper}', searching other drivers...")
                
                # Fallback: search in all drivers (prefer non-MME if no preferred driver)
                # Try exact match - prefer non-MME first
                non_mme_match = None
                mme_match = None
                
                for i, device in enumerate(devices):
                    if self.device_name == device['name'] and device['max_output_channels'] > 0:
                        if self.preferred_driver and is_api_device(device, self.preferred_driver.upper()):
                            # Already checked preferred driver above, skip
                            continue
                        elif not is_mme_device(device):
                            if non_mme_match is None:
                                non_mme_match = i
                        elif mme_match is None:
                            mme_match = i
                
                if non_mme_match is not None:
                    logger.info(f"Found exact match (non-MME): '{devices[non_mme_match]['name']}'")
                    return non_mme_match
                
                # Try partial match - prefer non-MME first
                non_mme_partial = None
                mme_partial = None
                
                for i, device in enumerate(devices):
                    if (self.device_name.lower() in device['name'].lower() and 
                        device['max_output_channels'] > 0):
                        if self.preferred_driver and is_api_device(device, self.preferred_driver.upper()):
                            # Already checked preferred driver above, skip
                            continue
                        elif not is_mme_device(device):
                            if non_mme_partial is None:
                                non_mme_partial = i
                                logger.info(f"Found partial match (non-MME): '{device['name']}'")
                        elif mme_partial is None:
                            mme_partial = i
                
                if non_mme_partial is not None:
                    return non_mme_partial
                if mme_partial is not None:
                    logger.info(f"Found partial match (MME, fallback): '{devices[mme_partial]['name']}'")
                    return mme_partial
                if mme_match is not None:
                    logger.info(f"Found exact match (MME, fallback): '{devices[mme_match]['name']}'")
                    return mme_match
                
                logger.warning(f"Audio device '{self.device_name}' not found. Falling back to system default.")
            except Exception as e:
                logger.error(f"Error searching for devices: {e}")
        
        # 3. Fallback to default (None)
        return None

    async def play(self, source: Any) -> None:
        """
        Plays the audio file at the given path using sounddevice.
        """
        # DRY-RUN mode: skip playback
        from src.config import Config
        if Config.DRY_RUN or source == "[DRY-RUN-AUDIO]":
            logger.info("[DRY-RUN] Would play audio")
            return
        
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
