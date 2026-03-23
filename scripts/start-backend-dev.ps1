# ============================================================================
# AHDUNYI Terminal PRO - Backend Development Startup Script (PowerShell)
# ============================================================================
# Starts the backend server in development mode
# ============================================================================

Write-Host "🚀 Starting AHDUNYI Terminal PRO Backend (Development Mode)..." -ForegroundColor Green
Write-Host "📊 Environment: DEVELOPMENT" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# Set environment
$env:ENVIRONMENT = "development"

# Change to server directory
Set-Location "$PSScriptRoot\..\server"

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check if dependencies are installed
if (-not (Test-Path "requirements.txt")) {
    Write-Host "❌ requirements.txt not found" -ForegroundColor Red
    exit 1
}

# Install dependencies if needed
Write-Host "📦 Checking Python dependencies..." -ForegroundColor Cyan
python -m pip install -r requirements.txt --quiet

# Start the server
Write-Host "🌐 Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload