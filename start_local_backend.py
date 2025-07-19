"""
Quick start script for local backend
This bypasses some production dependencies for quick local testing
"""
import subprocess
import sys
import os

print("=" * 60)
print("STARTING LOCAL BACKEND")
print("=" * 60)

# Set environment variables for local development
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "local-dev-secret-key-not-for-production"
os.environ["ENVIRONMENT"] = "development"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8080,https://cox-tree-quote-app.web.app"

# Try to install minimal dependencies
print("\nInstalling minimal dependencies...")
minimal_deps = [
    "fastapi",
    "uvicorn",
    "python-multipart",
    "python-dotenv",
    "pydantic",
    "pydantic-settings",
    "sqlalchemy",
    "aiosqlite",
    "python-jose[cryptography]",
    "passlib[bcrypt]",
    "httpx",
    "structlog"
]

for dep in minimal_deps:
    print(f"Installing {dep}...")
    subprocess.run([sys.executable, "-m", "pip", "install", dep], capture_output=True)

print("\n✓ Dependencies installed!")

# Create a minimal main.py for local testing
minimal_main = '''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="Tree Service API - Local")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory user storage for testing
users_db = {
    "admin": {
        "username": "admin",
        "password": "AdminPass123!",  # In real app, this would be hashed
        "role": "admin",
        "email": "admin@coxtreeservice.com",
        "full_name": "System Administrator"
    }
}

class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    full_name: str
    role: str = "estimator"

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/")
async def root():
    return {"app": "Tree Service API", "version": "0.1.0-local", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.1.0-local"}

@app.post("/api/auth/register")
async def register(user: UserCreate):
    if user.username in users_db:
        return {"error": "User already registered"}, 400
    
    users_db[user.username] = {
        "username": user.username,
        "password": user.password,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role
    }
    
    return {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "access_token": f"fake-jwt-token-for-{user.username}"
    }

@app.post("/api/auth/login")
async def login(form_data: LoginRequest):
    if form_data.username not in users_db:
        return {"error": "Invalid credentials"}, 401
    
    user = users_db[form_data.username]
    if user["password"] != form_data.password:
        return {"error": "Invalid credentials"}, 401
    
    return {
        "access_token": f"fake-jwt-token-for-{form_data.username}",
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@app.get("/api/auth/users")
async def get_users():
    return list(users_db.values())

@app.get("/api/estimates/")
async def get_estimates():
    return []

@app.get("/api/dashboard/stats")
async def dashboard_stats():
    return {
        "today_estimates": 0,
        "pending_approval": 0,
        "month_revenue": 0,
        "active_users": len(users_db)
    }

print("\\n✓ Local API running at http://localhost:8000")
print("\\nDefault admin credentials:")
print("Username: admin")
print("Password: AdminPass123!")
'''

# Write the minimal main.py
with open("src/main_local.py", "w") as f:
    f.write(minimal_main)

print("\nStarting local backend...")
print("-" * 60)
print("Backend will be available at: http://localhost:8000")
print("API endpoints at: http://localhost:8000/api")
print("Health check at: http://localhost:8000/health")
print("-" * 60)

# Start the server
subprocess.run([sys.executable, "-m", "uvicorn", "src.main_local:app", "--reload", "--host", "127.0.0.1", "--port", "8000"])