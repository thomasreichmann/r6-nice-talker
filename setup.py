#!/usr/bin/env python3
"""
Automated setup script for R6 Nice Talker.
Handles dependency installation, configuration, and validation.

Usage:
    python setup.py
"""
import sys
import os
import subprocess
import shutil
from pathlib import Path


class SetupManager:
    """Manages automated setup process."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.errors = []
    
    def print_header(self, text):
        """Print a section header."""
        print("\n" + "=" * 60)
        print(text)
        print("=" * 60)
    
    def print_step(self, text):
        """Print a setup step."""
        print(f"\n→ {text}")
    
    def print_success(self, text):
        """Print a success message."""
        print(f"  ✓ {text}")
    
    def print_error(self, text):
        """Print an error message."""
        print(f"  ✗ {text}")
        self.errors.append(text)
    
    def print_warning(self, text):
        """Print a warning message."""
        print(f"  ⚠ {text}")
    
    def check_python_version(self):
        """Check if Python version is >= 3.10."""
        self.print_step("Checking Python version...")
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 10:
            self.print_success(f"Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.print_error(f"Python {version.major}.{version.minor} (need >= 3.10)")
            return False
    
    def check_pip(self):
        """Check if pip is available."""
        self.print_step("Checking pip...")
        
        try:
            import pip
            self.print_success(f"pip {pip.__version__}")
            return True
        except ImportError:
            self.print_error("pip not found")
            return False
    
    def create_venv(self):
        """Create virtual environment if it doesn't exist."""
        self.print_step("Setting up virtual environment...")
        
        if self.venv_path.exists():
            self.print_warning("Virtual environment already exists (skipping)")
            return True
        
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_path)],
                check=True
            )
            self.print_success(f"Created virtual environment at {self.venv_path}")
            return True
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to create virtual environment: {e}")
            return False
    
    def get_venv_python(self):
        """Get path to Python executable in venv."""
        if sys.platform == "win32":
            return self.venv_path / "Scripts" / "python.exe"
        else:
            return self.venv_path / "bin" / "python"
    
    def get_venv_pip(self):
        """Get path to pip executable in venv."""
        if sys.platform == "win32":
            return self.venv_path / "Scripts" / "pip.exe"
        else:
            return self.venv_path / "bin" / "pip"
    
    def install_dependencies(self):
        """Install dependencies from requirements.txt."""
        self.print_step("Installing dependencies...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            self.print_error("requirements.txt not found")
            return False
        
        try:
            pip_exe = self.get_venv_pip() if self.venv_path.exists() else "pip"
            
            result = subprocess.run(
                [str(pip_exe), "install", "-r", str(requirements_file)],
                check=True,
                capture_output=True,
                text=True
            )
            
            self.print_success("Dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to install dependencies: {e}")
            if e.stderr:
                print(f"    {e.stderr[:200]}")
            return False
    
    def setup_env_file(self):
        """Copy env.example to .env if it doesn't exist."""
        self.print_step("Setting up configuration file...")
        
        env_file = self.project_root / ".env"
        env_example = self.project_root / "env.example"
        
        if env_file.exists():
            self.print_warning(".env already exists (skipping)")
            return True
        
        if not env_example.exists():
            self.print_error("env.example not found")
            return False
        
        try:
            shutil.copy(env_example, env_file)
            self.print_success("Created .env from env.example")
            print("    ⚠ Remember to edit .env with your API keys!")
            return True
        except Exception as e:
            self.print_error(f"Failed to copy env.example: {e}")
            return False
    
    def run_health_check(self):
        """Run the health check system."""
        self.print_step("Running health check...")
        
        try:
            python_exe = self.get_venv_python() if self.venv_path.exists() else sys.executable
            
            result = subprocess.run(
                [str(python_exe), "-m", "src.health_check"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )
            
            # Print health check output
            print(result.stdout)
            
            if result.returncode == 0:
                self.print_success("Health check passed")
                return True
            elif result.returncode == 2:
                self.print_warning("Health check passed with warnings")
                return True
            else:
                self.print_error(f"Health check failed {result.stderr}")
                return False
        except Exception as e:
            self.print_error(f"Failed to run health check: {e}")
            return False
    
    def print_next_steps(self):
        """Print next steps for the user."""
        self.print_header("Setup Complete!")
        
        print("\nNext steps:")
        print("\n1. Edit your .env file with API keys:")
        print(f"     {self.project_root / '.env'}")
        
        print("\n2. Activate the virtual environment:")
        if sys.platform == "win32":
            print(f"     .\\venv\\Scripts\\activate")
        else:
            print(f"     source venv/bin/activate")
        
        print("\n3. Run the bot:")
        print("     python main.py")
        
        print("\n4. Test components:")
        print("     python tools/test_tts.py --text \"Hello\" --provider pyttsx3")
        print("     python tools/test_messages.py --dry-run --list-personas")
        
        print("\nFor more help, see:")
        print("  - CONTRIBUTING.md")
        print("  - docs/DEVELOPMENT.md")
        print("")
    
    def run_setup(self):
        """Run the complete setup process."""
        self.print_header("R6 Nice Talker - Automated Setup")
        
        print("\nThis script will:")
        print("  1. Check Python version")
        print("  2. Create virtual environment")
        print("  3. Install dependencies")
        print("  4. Setup configuration")
        print("  5. Run health check")
        
        input("\nPress Enter to continue (Ctrl+C to cancel)...")
        
        # Run setup steps
        steps = [
            ("Check Python version", self.check_python_version),
            ("Check pip", self.check_pip),
            ("Create virtual environment", self.create_venv),
            ("Install dependencies", self.install_dependencies),
            ("Setup configuration", self.setup_env_file),
            ("Run health check", self.run_health_check),
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                self.print_header("Setup Failed")
                print(f"\n❌ Setup failed at: {step_name}")
                if self.errors:
                    print("\nErrors encountered:")
                    for error in self.errors:
                        print(f"  - {error}")
                print("\nPlease fix the errors and run setup again.")
                return 1
        
        # Success
        self.print_next_steps()
        return 0


def main():
    """Main entry point."""
    setup = SetupManager()
    exit_code = setup.run_setup()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

