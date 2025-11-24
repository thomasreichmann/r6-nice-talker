"""
Health check system for validating setup and configuration.
Run with: python -m src.health_check
"""
import sys
import os
import subprocess
from pathlib import Path
from typing import List, Tuple
import logging

# Setup minimal logging for health check
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class HealthCheck:
    """Validates system setup and configuration."""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
        self.results: List[Tuple[str, bool, str]] = []
    
    def check(self, name: str, passed: bool, message: str, warning: bool = False):
        """Record a check result."""
        self.results.append((name, passed, message))
        
        # Use ASCII-safe characters for Windows compatibility
        if passed:
            self.checks_passed += 1
            status = "[OK]" if not warning else "[WARN]"
            color = "\033[92m" if not warning else "\033[93m"
        else:
            self.checks_failed += 1
            status = "[FAIL]"
            color = "\033[91m"
        
        reset = "\033[0m"
        
        # Safe print that handles encoding issues
        try:
            print(f"{color}{status}{reset} {name}: {message}")
        except UnicodeEncodeError:
            # Fallback without color codes for problematic terminals
            print(f"{status} {name}: {message}")
        
        if warning and passed:
            self.warnings += 1
    
    def check_python_version(self):
        """Check Python version >= 3.10."""
        version = sys.version_info
        passed = version.major == 3 and version.minor >= 10
        
        if passed:
            msg = f"Python {version.major}.{version.minor}.{version.micro}"
        else:
            msg = f"Python {version.major}.{version.minor}.{version.micro} (need >= 3.10)"
        
        self.check("Python Version", passed, msg)
        return passed
    
    def check_packages(self):
        """Check if all required packages are installed."""
        try:
            with open("requirements.txt", "r") as f:
                requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            
            missing = []
            for req in requirements:
                # Extract package name (before ==, >=, etc.)
                pkg_name = req.split("==")[0].split(">=")[0].split("<")[0].strip()
                
                # Special handling for some packages
                import_name = {
                    "python-dotenv": "dotenv",
                    "opencv-python": "cv2",
                    "pydirectinput-rgx": "pydirectinput",
                    "pillow": "PIL",
                }.get(pkg_name, pkg_name)
                
                try:
                    __import__(import_name)
                except ImportError:
                    missing.append(pkg_name)
            
            if missing:
                self.check("Package Installation", False, f"Missing: {', '.join(missing)}")
                return False
            else:
                self.check("Package Installation", True, f"{len(requirements)} packages installed")
                return True
                
        except FileNotFoundError:
            self.check("Package Installation", False, "requirements.txt not found")
            return False
        except Exception as e:
            self.check("Package Installation", False, f"Error checking packages: {e}")
            return False
    
    def check_env_file(self):
        """Check if .env file exists."""
        env_path = Path(".env")
        
        if env_path.exists():
            self.check(".env File", True, "Found")
            return True
        else:
            self.check(".env File", False, "Missing (copy env.example to .env)")
            return False
    
    def check_api_keys(self):
        """Check if API keys are configured."""
        from src.config import Config
        
        warnings = []
        
        # OpenAI key
        if Config.MESSAGE_PROVIDER_TYPE == "chatgpt":
            if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY.startswith("sk-YOUR"):
                self.check("OpenAI API Key", False, "Not configured (needed for chatgpt provider)")
                return False
            else:
                # Test key format
                if not Config.OPENAI_API_KEY.startswith("sk-"):
                    self.check("OpenAI API Key", False, "Invalid format (should start with 'sk-')")
                    return False
                else:
                    self.check("OpenAI API Key", True, "Configured")
        else:
            self.check("OpenAI API Key", True, "Not required (provider: {})".format(Config.MESSAGE_PROVIDER_TYPE), warning=True)
        
        # ElevenLabs key
        if Config.TTS_PROVIDER == "elevenlabs":
            if not Config.ELEVENLABS_API_KEY:
                self.check("ElevenLabs API Key", False, "Not configured (needed for elevenlabs TTS)")
                return False
            else:
                self.check("ElevenLabs API Key", True, "Configured")
        else:
            self.check("ElevenLabs API Key", True, "Not required (provider: {})".format(Config.TTS_PROVIDER), warning=True)
        
        return True
    
    def check_tesseract(self):
        """Check if Tesseract is installed and accessible."""
        from src.config import Config
        
        if Config.VISION_ENGINE != "tesseract":
            self.check("Tesseract OCR", True, "Not required (engine: {})".format(Config.VISION_ENGINE), warning=True)
            return True
        
        tess_path = Config.TESSERACT_PATH
        
        if not Path(tess_path).exists():
            self.check("Tesseract OCR", False, f"Not found at {tess_path}")
            return False
        
        # Try to run tesseract
        try:
            result = subprocess.run(
                [tess_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version = result.stdout.split("\n")[0]
                self.check("Tesseract OCR", True, version)
                return True
            else:
                self.check("Tesseract OCR", False, "Failed to execute")
                return False
                
        except Exception as e:
            self.check("Tesseract OCR", False, f"Error: {e}")
            return False
    
    def check_audio_devices(self):
        """Check for audio devices."""
        try:
            import sounddevice as sd
            
            devices = sd.query_devices()
            output_devices = [d for d in devices if d['max_output_channels'] > 0]
            
            if output_devices:
                self.check("Audio Devices", True, f"Found {len(output_devices)} output device(s)")
                
                # Check for virtual cable
                from src.config import Config
                if Config.AUDIO_OUTPUT_DEVICE_NAME:
                    found = False
                    for d in devices:
                        if Config.AUDIO_OUTPUT_DEVICE_NAME.lower() in d['name'].lower():
                            found = True
                            break
                    
                    if found:
                        self.check("Virtual Audio Cable", True, f"Found: {Config.AUDIO_OUTPUT_DEVICE_NAME}")
                    else:
                        self.check("Virtual Audio Cable", False, f"Not found: {Config.AUDIO_OUTPUT_DEVICE_NAME}")
                        return False
                else:
                    self.check("Virtual Audio Cable", True, "Using system default", warning=True)
                
                return True
            else:
                self.check("Audio Devices", False, "No output devices found")
                return False
                
        except Exception as e:
            self.check("Audio Devices", False, f"Error: {e}")
            return False
    
    def check_rois(self):
        """Check if ROIs are configured."""
        from src.config import Config
        
        if not Config.VISION_ROIS:
            self.check("ROI Configuration", True, "No ROIs configured (vision disabled)", warning=True)
            return True
        
        roi_count = len(Config.VISION_ROIS)
        self.check("ROI Configuration", True, f"{roi_count} ROI(s) configured")
        return True
    
    def check_prompts(self):
        """Check if prompts.json is valid."""
        try:
            import json
            
            with open("prompts.json", "r", encoding="utf-8") as f:
                prompts = json.load(f)
            
            if not isinstance(prompts, list):
                self.check("prompts.json", False, "Invalid format (should be array)")
                return False
            
            if len(prompts) == 0:
                self.check("prompts.json", False, "Empty (no personas defined)")
                return False
            
            # Check structure
            for i, persona in enumerate(prompts):
                if "name" not in persona:
                    self.check("prompts.json", False, f"Persona {i} missing 'name' field")
                    return False
                
                if "prompts" not in persona and "prompt" not in persona:
                    self.check("prompts.json", False, f"Persona {i} missing 'prompts' field")
                    return False
            
            self.check("prompts.json", True, f"{len(prompts)} persona(s) defined")
            return True
            
        except FileNotFoundError:
            self.check("prompts.json", False, "File not found")
            return False
        except json.JSONDecodeError as e:
            self.check("prompts.json", False, f"Invalid JSON: {e}")
            return False
        except Exception as e:
            self.check("prompts.json", False, f"Error: {e}")
            return False
    
    def run_all_checks(self, verbose: bool = False):
        """Run all health checks."""
        print("\n" + "=" * 60)
        print("R6 Nice Talker - Health Check")
        print("=" * 60 + "\n")
        
        # Critical checks
        print("Critical Checks:")
        self.check_python_version()
        self.check_packages()
        self.check_env_file()
        
        print("\nConfiguration Checks:")
        self.check_api_keys()
        self.check_prompts()
        
        print("\nOptional Components:")
        self.check_tesseract()
        self.check_audio_devices()
        self.check_rois()
        
        # Summary
        print("\n" + "=" * 60)
        print("Summary:")
        print(f"  Passed: {self.checks_passed}")
        if self.warnings > 0:
            print(f"  Warnings: {self.warnings}")
        if self.checks_failed > 0:
            print(f"  Failed: {self.checks_failed}")
        print("=" * 60 + "\n")
        
        if self.checks_failed > 0:
            print("[FAIL] Health check failed. Please fix the issues above.")
            return 1
        elif self.warnings > 0:
            print("[WARN] Health check passed with warnings.")
            return 2
        else:
            print("[OK] All checks passed! You're ready to run the bot.")
            return 0


def main():
    """Main entry point for health check."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run health checks for R6 Nice Talker")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix common issues (not implemented)")
    
    args = parser.parse_args()
    
    if args.fix:
        print("⚠ Auto-fix not implemented yet. Please fix issues manually.")
        return 1
    
    health_check = HealthCheck()
    exit_code = health_check.run_all_checks(verbose=args.verbose)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()


