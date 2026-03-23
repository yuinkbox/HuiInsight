# ============================================================================
# AHDUNYI Terminal PRO - Frontend Development Startup Script (PowerShell)
# ============================================================================
# Starts the frontend development server
# ============================================================================

Write-Host "🚀 Starting AHDUNYI Terminal PRO Frontend (Development Mode)..." -ForegroundColor Green
Write-Host "📊 Environment: DEVELOPMENT" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# Change to web client directory
Set-Location "$PSScriptRoot\..\client\web"

# Check if Node.js is available
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Node.js not found"
    }
    Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check if npm is available
try {
    $npmVersion = npm --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "npm not found"
    }
    Write-Host "✅ npm found: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ npm not found. Please install npm" -ForegroundColor Red
    exit 1
}

# Install dependencies if needed
Write-Host "📦 Checking npm dependencies..." -ForegroundColor Cyan
npm install --silent

# Start the development server
Write-Host "🌐 Starting Vite development server on http://localhost:5173" -ForegroundColor Green
Write-Host "🔗 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

npm run dev