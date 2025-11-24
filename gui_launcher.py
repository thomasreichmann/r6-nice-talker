"""
GUI Launcher - Main entry point for all GUI tools.
Run with: python gui_launcher.py
"""
import dearpygui.dearpygui as dpg
import sys
import subprocess
from pathlib import Path

# Add to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from gui.components import setup_theme, COLORS


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
    
    def create_ui(self):
        """Create the launcher UI."""
        with dpg.window(label="R6 Nice Talker - GUI Tools", tag="main_window", width=700, height=500):
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
            with dpg.child_window(height=200, width=-1):
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

