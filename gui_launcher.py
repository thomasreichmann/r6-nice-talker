"""
GUI Launcher - Main entry point for all GUI tools.
Run with: python gui_launcher.py
"""
import dearpygui.dearpygui as dpg
import sys
import subprocess
import asyncio
import threading
import tempfile
import os
import numpy as np
import soundfile as sf
from pathlib import Path

# Add to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from gui.components import setup_theme, COLORS
from src.voice import SoundDevicePlayer
from src.config import Config


class GUILauncher:
    """Main launcher for GUI tools."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
    
    def launch_analytics(self):
        """Launch analytics dashboard."""
        try:
            subprocess.Popen([sys.executable, "gui/analytics_dashboard.py"])
        except Exception as e:
            print(f"Error launching analytics: {e}")
    
    def launch_tool(self, tool_name, script_path):
        """Generic tool launcher."""
        try:
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            print(f"Error launching {tool_name}: {e}")
    
    def play_test_sound(self):
        """Generate and play a test sound through the audio player."""
        def _play_async():
            """Run async audio playback in a separate thread."""
            try:
                # Generate a simple test tone (440Hz sine wave for 1 second)
                sample_rate = 44100
                duration = 1.0  # seconds
                frequency = 440  # A4 note
                
                t = np.linspace(0, duration, int(sample_rate * duration), False)
                tone = np.sin(2 * np.pi * frequency * t)
                
                # Convert to stereo (2 channels)
                tone_stereo = np.column_stack([tone, tone])
                
                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                temp_path = temp_file.name
                temp_file.close()
                
                sf.write(temp_path, tone_stereo, sample_rate, format='WAV')
                
                # Play through audio player
                async def play():
                    player = SoundDevicePlayer(
                        device_name=Config.AUDIO_OUTPUT_DEVICE_NAME,
                        device_index=Config.AUDIO_OUTPUT_DEVICE_INDEX,
                        monitor=Config.AUDIO_MONITORING,
                        preferred_driver=Config.AUDIO_PREFERRED_DRIVER
                    )
                    await player.play(temp_path)
                
                asyncio.run(play())
                
                # Cleanup temp file (player.play should delete it, but just in case)
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
                    
            except Exception as e:
                print(f"Error playing test sound: {e}")
        
        # Run in a separate thread to avoid blocking the GUI
        thread = threading.Thread(target=_play_async, daemon=True)
        thread.start()
    
    def create_ui(self):
        """Create the launcher UI."""
        with dpg.window(label="R6 Nice Talker - GUI Tools", tag="main_window", width=700, height=550):
            # Header
            dpg.add_text("R6 Nice Talker", color=COLORS['accent'])
            dpg.add_text("Developer Tools & Utilities", color=COLORS['text_dim'])
            dpg.add_separator()
            
            # Tools Grid
            dpg.add_text("Available Tools:", color=COLORS['accent'])
            dpg.add_spacer(height=10)
            
            # Analytics Dashboard
            with dpg.group(horizontal=True):
                with dpg.child_window(height=100, width=300):
                    dpg.add_text("Analytics Dashboard", color=COLORS['success'])
                    dpg.add_text("View costs, usage, and trends", color=COLORS['text_dim'], wrap=280)
                    dpg.add_button(label="Launch", callback=self.launch_analytics)
            
            dpg.add_spacer(height=10)
            
            # Testing Tools
            with dpg.child_window(height=230, width=-1):
                dpg.add_text("Testing Tools", color=COLORS['accent'])
                dpg.add_separator()
                
                # TTS Test
                with dpg.group(horizontal=True):
                    dpg.add_text("Test TTS:")
                    dpg.add_button(
                        label="Launch",
                        callback=lambda: self.launch_tool("TTS Test", "tools/test_tts.py")
                    )
                
                # Message Test
                with dpg.group(horizontal=True):
                    dpg.add_text("Test Messages:")
                    dpg.add_button(
                        label="Launch",
                        callback=lambda: self.launch_tool("Message Test", "tools/test_messages.py")
                    )
                
                # Vision Test
                with dpg.group(horizontal=True):
                    dpg.add_text("Test Vision:")
                    dpg.add_button(
                        label="Launch",
                        callback=lambda: self.launch_tool("Vision Test", "tools/test_vision.py")
                    )
                
                # Typer Test
                with dpg.group(horizontal=True):
                    dpg.add_text("Test Typer:")
                    dpg.add_button(
                        label="Launch",
                        callback=lambda: self.launch_tool("Typer Test", "tools/test_typer.py")
                    )
                
                # Audio Test Sound
                with dpg.group(horizontal=True):
                    dpg.add_text("Test Audio Player:")
                    dpg.add_button(
                        label="Play Test Sound",
                        callback=lambda: self.play_test_sound()
                    )
            
            dpg.add_spacer(height=10)
            
            # Health Check
            with dpg.group(horizontal=True):
                dpg.add_text("System Health Check:")
                dpg.add_button(
                    label="Run",
                    callback=lambda: subprocess.run([sys.executable, "-m", "src.health_check"])
                )
            
            dpg.add_separator()
            
            # Footer
            dpg.add_text("Note: Additional GUI tools (Config Editor, Prompt Editor, etc.)", color=COLORS['text_dim'])
            dpg.add_text("follow the same pattern and can be added to this launcher.", color=COLORS['text_dim'])
            dpg.add_spacer(height=10)
            dpg.add_text("See CONTRIBUTING.md and docs/DEVELOPMENT.md for more info.", color=COLORS['text_dim'])
    
    def run(self):
        """Run the launcher."""
        dpg.create_context()
        setup_theme()
        
        self.create_ui()
        
        dpg.create_viewport(title="R6 Nice Talker - GUI Launcher", width=750, height=550)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        dpg.start_dearpygui()
        dpg.destroy_context()


def main():
    """Main entry point."""
    launcher = GUILauncher()
    launcher.run()


if __name__ == "__main__":
    main()

