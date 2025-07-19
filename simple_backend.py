"""
Simple backend for immediate testing
This provides just enough functionality to test the app
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import datetime
import json

app = FastAPI(title="Tree Service API - Simple")

# Enable CORS for all origins during testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage
users = {}
estimates = []
estimate_counter = 1

# Pre-create admin users
users["admin"] = {
    "username": "admin",
    "password": "AdminPass123!",
    "email": "admin@coxtreeservice.com",
    "full_name": "System Administrator",
    "role": "admin",
    "id": 1
}

users["Cameroncox1993"] = {
    "username": "Cameroncox1993",
    "password": "CoxTree#2024!Admin",
    "email": "cameron@coxtreeservice.com",
    "full_name": "Cameron Cox",
    "role": "admin",
    "id": 2
}

# Models
class LoginForm(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    full_name: str
    role: str = "estimator"

class EstimateCreate(BaseModel):
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    service_address: str
    service_date: Optional[str] = None
    items: List[dict] = []
    notes: Optional[str] = None
    total_price: float = 0.0

# Root endpoint
@app.get("/")
def root():
    return {
        "app": "Tree Service API",
        "version": "0.1.0-simple",
        "status": "running",
        "message": "Simple backend for testing"
    }

# Health check
@app.get("/health")
def health():
    return {"status": "healthy", "version": "0.1.0-simple"}

# Auth endpoints
@app.post("/api/auth/login")
def login(form_data: LoginForm):
    user = users.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "access_token": f"fake-token-{form_data.username}",
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "full_name": user["full_name"]
        }
    }

@app.post("/api/auth/register")
def register(user_data: UserCreate):
    if user_data.username in users:
        raise HTTPException(status_code=400, detail="User already registered")
    
    user_id = len(users) + 1
    users[user_data.username] = {
        "id": user_id,
        "username": user_data.username,
        "password": user_data.password,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "role": user_data.role
    }
    
    return {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "role": user_data.role
    }

@app.get("/api/auth/users")
def get_users():
    return [
        {
            "id": u["id"],
            "username": u["username"],
            "email": u["email"],
            "full_name": u["full_name"],
            "role": u["role"]
        }
        for u in users.values()
    ]

# Dashboard endpoints
@app.get("/api/dashboard/stats")
def dashboard_stats():
    today = datetime.date.today()
    today_estimates = [e for e in estimates if e.get("created_at", "").startswith(str(today))]
    pending = [e for e in estimates if e.get("status") == "pending"]
    
    return {
        "today_estimates": len(today_estimates),
        "pending_approval": len(pending),
        "month_revenue": sum(e.get("total_price", 0) for e in estimates),
        "active_users": len(users)
    }

# Estimates endpoints
@app.get("/api/estimates/")
def get_estimates():
    return estimates

@app.get("/api/estimates/recent")
def get_recent_estimates():
    return estimates[:5]  # Return last 5 estimates

@app.post("/api/estimates/")
def create_estimate(estimate: EstimateCreate):
    global estimate_counter
    new_estimate = {
        "id": estimate_counter,
        "estimate_number": f"EST-{estimate_counter:04d}",
        "status": "pending",
        "created_at": datetime.datetime.now().isoformat(),
        **estimate.dict()
    }
    estimates.append(new_estimate)
    estimate_counter += 1
    return new_estimate

@app.get("/api/estimates/{estimate_id}")
def get_estimate(estimate_id: int):
    for e in estimates:
        if e["id"] == estimate_id:
            return e
    raise HTTPException(status_code=404, detail="Estimate not found")

@app.post("/api/estimates/{estimate_id}/approve")
def approve_estimate(estimate_id: int):
    for e in estimates:
        if e["id"] == estimate_id:
            e["status"] = "approved"
            e["approved_at"] = datetime.datetime.now().isoformat()
            return e
    raise HTTPException(status_code=404, detail="Estimate not found")

@app.post("/api/estimates/{estimate_id}/reject")
def reject_estimate(estimate_id: int):
    for e in estimates:
        if e["id"] == estimate_id:
            e["status"] = "rejected"
            e["rejected_at"] = datetime.datetime.now().isoformat()
            return e
    raise HTTPException(status_code=404, detail="Estimate not found")

# Costs/Pricing endpoints
@app.get("/api/costs/")
def get_costs():
    return {
        "labor_rates": {
            "climber": 45.00,
            "groundsman": 25.00,
            "driver": 25.00
        },
        "overhead_percent": 25.0,
        "profit_percent": 35.0,
        "safety_buffer_percent": 10.0,
        "vehicle_rate_per_mile": 0.65,
        "equipment_rates": {
            "chipper": 75.00,
            "bucket_truck": 125.00,
            "stump_grinder": 85.00
        }
    }

@app.post("/api/costs/")
def update_costs(costs: dict):
    # In a real app, this would save to database
    return costs

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("SIMPLE BACKEND STARTING")
    print("="*60)
    print("\nAdmin credentials:")
    print("Username: admin")
    print("Password: AdminPass123!")
    print("\nAPI will be available at: http://localhost:8001")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8001)