# R6 Nice Talker - Windows Setup Script
# Run with: powershell -ExecutionPolicy Bypass -File setup.ps1

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "R6 Nice Talker - Windows Setup" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Warning: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "Some features (like Tesseract installation check) may not work properly`n" -ForegroundColor Yellow
}

# Check Python
Write-Host "→ Checking Python installation..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $pythonVersion = python --version
    Write-Host "  ✓ Found: $pythonVersion" -ForegroundColor Green
    
    # Check version
    $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
    if ($versionMatch) {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        
        if ($major -eq 3 -and $minor -ge 10) {
            Write-Host "  ✓ Version OK (>= 3.10)" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Python 3.10+ required (found $major.$minor)" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "  ✗ Python not found" -ForegroundColor Red
    Write-Host "    Please install Python 3.10+ from https://python.org" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "`n→ Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  ⚠ Virtual environment already exists (skipping)" -ForegroundColor Yellow
} else {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Created virtual environment" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate venv and install dependencies
Write-Host "`n→ Installing dependencies..." -ForegroundColor Yellow
& .\venv\Scripts\python.exe -m pip install --upgrade pip | Out-Null
& .\venv\Scripts\pip.exe install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Setup .env
Write-Host "`n→ Setting up configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  ⚠ .env already exists (skipping)" -ForegroundColor Yellow
} else {
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Host "  ✓ Created .env from env.example" -ForegroundColor Green
        Write-Host "    ⚠ Remember to edit .env with your API keys!" -ForegroundColor Yellow
    } else {
        Write-Host "  ✗ env.example not found" -ForegroundColor Red
    }
}

# Check Tesseract
Write-Host "`n→ Checking Tesseract OCR..." -ForegroundColor Yellow
$tessPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"
if (Test-Path $tessPath) {
    $tessVersion = & $tessPath --version 2>&1 | Select-Object -First 1
    Write-Host "  ✓ Found: $tessVersion" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Tesseract not found at $tessPath" -ForegroundColor Yellow
    Write-Host "    Install from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Yellow
}

# Check Virtual Audio Cable
Write-Host "`n→ Checking Virtual Audio Cable..." -ForegroundColor Yellow
$audioDevices = Get-CimInstance Win32_SoundDevice | Select-Object -ExpandProperty Name
$hasCable = $audioDevices -match "CABLE|VB-Audio"

if ($hasCable) {
    Write-Host "  ✓ Virtual audio device found" -ForegroundColor Green
} else {
    Write-Host "  ⚠ No virtual audio cable detected" -ForegroundColor Yellow
    Write-Host "    For voice injection, install VB-Audio Virtual Cable:" -ForegroundColor Yellow
    Write-Host "    https://vb-audio.com/Cable/" -ForegroundColor Yellow
}

# Run health check
Write-Host "`n→ Running health check..." -ForegroundColor Yellow
& .\venv\Scripts\python.exe -m src.health_check

# Summary
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Edit .env with your API keys" -ForegroundColor White
Write-Host "  2. Activate virtual environment: .\venv\Scripts\activate" -ForegroundColor White
Write-Host "  3. Run the bot: python main.py" -ForegroundColor White
Write-Host "  4. Test components: python tools\test_tts.py --help`n" -ForegroundColor White

Write-Host "For more help, see CONTRIBUTING.md and docs\DEVELOPMENT.md`n" -ForegroundColor Gray

