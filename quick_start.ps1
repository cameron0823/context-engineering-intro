# Quick Start Script for Windows PowerShell
# Tree Service Estimating App

Write-Host "=== Tree Service Estimating App - Quick Start ===" -ForegroundColor Green
Write-Host ""

# Change to project directory
Set-Location $PSScriptRoot

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file first." -ForegroundColor Yellow
    exit 1
}

Write-Host "Step 1: Creating minimal dependencies file..." -ForegroundColor Cyan
@"
# Minimal dependencies for quick start
fastapi
uvicorn[standard]
python-multipart
sqlalchemy
alembic
pydantic
pydantic-settings
python-dotenv
python-jose[cryptography]
passlib[bcrypt]
httpx
tenacity
redis
prometheus-client
structlog
aiosqlite
"@ | Out-File -FilePath "requirements-quickstart.txt" -Encoding UTF8

Write-Host "Step 2: Installing dependencies..." -ForegroundColor Cyan
try {
    & venv_linux\Scripts\pip.exe install -r requirements-quickstart.txt
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    
    # Try with .venv instead
    if (Test-Path ".venv\Scripts\pip.exe") {
        Write-Host "Trying with .venv instead..." -ForegroundColor Yellow
        & .venv\Scripts\pip.exe install -r requirements-quickstart.txt
    } else {
        Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
        Write-Host "  python -m venv venv" -ForegroundColor White
        Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
        exit 1
    }
}

Write-Host ""
Write-Host "Step 3: Creating directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "uploads" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "alembic\versions" | Out-Null
Write-Host "✅ Directories created" -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Setting up SQLite database..." -ForegroundColor Cyan

# Backup .env and modify for SQLite
Copy-Item ".env" ".env.backup" -Force

$envContent = Get-Content ".env" -Raw
$envContent = $envContent -replace 'DATABASE_URL=postgresql://.*', 'DATABASE_URL=sqlite:///./treeservice.db'
$envContent | Out-File ".env" -Encoding UTF8

Write-Host "✅ Configured SQLite database" -ForegroundColor Green

Write-Host ""
Write-Host "Step 5: Creating test data script..." -ForegroundColor Cyan

# Create a simple test data script
@"
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from src.db.base import Base

async def init_db():
    engine = create_async_engine("sqlite+aiosqlite:///./treeservice.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Database tables created!")

asyncio.run(init_db())
"@ | Out-File -FilePath "init_db.py" -Encoding UTF8

Write-Host ""
Write-Host "Step 6: Initializing database..." -ForegroundColor Cyan
try {
    if (Test-Path "venv_linux\Scripts\python.exe") {
        & venv_linux\Scripts\python.exe init_db.py
    } elseif (Test-Path ".venv\Scripts\python.exe") {
        & .venv\Scripts\python.exe init_db.py
    } else {
        python init_db.py
    }
    Write-Host "✅ Database initialized" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Database initialization failed, but continuing..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "="*50 -ForegroundColor Cyan
Write-Host "🚀 Setup complete! Starting the application..." -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Cyan
Write-Host ""
Write-Host "The app will be available at:" -ForegroundColor Yellow
Write-Host "  - API: http://localhost:8000" -ForegroundColor White
Write-Host "  - Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Health: http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the app
try {
    if (Test-Path "venv_linux\Scripts\uvicorn.exe") {
        & venv_linux\Scripts\uvicorn.exe src.main:app --reload --port 8000
    } elseif (Test-Path ".venv\Scripts\uvicorn.exe") {
        & .venv\Scripts\uvicorn.exe src.main:app --reload --port 8000
    } else {
        uvicorn src.main:app --reload --port 8000
    }
} finally {
    # Restore original .env
    if (Test-Path ".env.backup") {
        Move-Item ".env.backup" ".env" -Force
        Write-Host ""
        Write-Host "✅ Original .env file restored" -ForegroundColor Green
    }
}