name: "Tree Service Estimating Application - Production-Ready Implementation"
description: |

## Purpose
Build a production-ready tree service estimating application that provides accurate, real-time job quotes based on comprehensive cost calculations with deterministic formula pipeline, audit trails, and role-based access control.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Create a FastAPI-based estimating application where:
- Users calculate accurate job quotes using deterministic formula pipeline
- System tracks all costs with effective dating for historical accuracy
- Role-based permissions control access to cost data and features
- Real-time calculations update as inputs change
- Complete audit trail tracks every change for compliance
- 95% accuracy target with estimates within 10% of actual costs

## Why
- **Business value**: Streamlines quoting process, improves accuracy, reduces manual errors
- **Integration**: Works with QuickBooks for invoicing, Google Maps for travel calculations
- **Problems solved**: Eliminates spreadsheet errors, ensures consistent pricing, provides audit trail

## What
A web-based application with:
- Real-time cost calculation engine
- Role-based access (Admin, Manager, Estimator, Viewer)
- Mobile-responsive interface with offline capability
- External API integrations (QuickBooks, Google Maps, fuel prices)
- 7-year data retention with complete audit trails

### Success Criteria
- [ ] Deterministic formula pipeline produces consistent results
- [ ] Effective dating allows historical quote recreation
- [ ] Role-based permissions properly restrict access
- [ ] Real-time calculations update within 100ms
- [ ] API integrations handle rate limits gracefully
- [ ] Mobile interface works offline and syncs when online
- [ ] All tests pass with >80% coverage
- [ ] 99.9% uptime during business hours

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
  why: JWT-based authentication for role-based access
  
- url: https://fastapi.tiangolo.com/tutorial/dependencies/
  why: Dependency injection for permission checking
  
- url: https://docs.sqlalchemy.org/en/20/orm/versioning.html
  why: Temporal versioning patterns for effective dating
  
- url: https://docs.pydantic.dev/latest/concepts/validators/
  why: Complex validation for calculation inputs
  
- url: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/create-invoice
  why: QuickBooks invoice creation from estimates
  
- url: https://developers.google.com/maps/documentation/distance-matrix/distance-matrix
  why: Travel time and distance calculations
  
- url: https://docs.python.org/3/library/decimal.html
  why: Decimal precision for financial calculations
  
- url: https://github.com/tiangolo/full-stack-fastapi-postgresql
  why: Production FastAPI + PostgreSQL patterns
  
- doc: https://www.postgresql.org/docs/current/ddl-system-columns.html
  section: System Columns for audit trails
  critical: Use xmin/xmax for row versioning
  
- doc: https://martinfowler.com/articles/patterns-of-distributed-systems/two-phase-commit.html
  why: Pattern for ensuring calculation consistency
```

### Current Codebase tree
```bash
.
├── examples/
├── PRPs/
│   └── templates/
│       └── prp_base.md
├── INITIAL.md
├── CLAUDE.md
└── Tree_service_estimating_app.md
```

### Desired Codebase tree with files to be added
```bash
.
├── src/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── estimates.py        # Estimate CRUD endpoints
│   │   ├── costs.py            # Cost management endpoints
│   │   ├── reports.py          # Reporting endpoints
│   │   └── deps.py             # Dependencies (auth, permissions)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings management
│   │   ├── security.py         # JWT, password hashing
│   │   └── calculator.py       # Deterministic formula engine
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py             # Base SQLAlchemy model with audit
│   │   ├── user.py             # User model with roles
│   │   ├── estimate.py         # Estimate model
│   │   ├── costs.py            # Cost models with effective dating
│   │   └── audit.py            # Audit trail model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # User Pydantic schemas
│   │   ├── estimate.py         # Estimate schemas
│   │   ├── costs.py            # Cost schemas
│   │   └── calculation.py      # Calculation schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── calculation.py      # Business logic for calculations
│   │   ├── external_apis.py    # QuickBooks, Google Maps, fuel
│   │   └── audit.py            # Audit logging service
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py          # Database session management
│   │   └── init_db.py          # Database initialization
│   └── utils/
│       ├── __init__.py
│       ├── rounding.py         # $5 rounding utilities
│       └── cache.py            # Caching for API responses
├── alembic/
│   ├── alembic.ini             # Alembic configuration
│   └── versions/               # Database migrations
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_auth.py            # Authentication tests
│   ├── test_calculator.py      # Formula engine tests
│   ├── test_estimates.py       # Estimate endpoint tests
│   ├── test_costs.py           # Cost management tests
│   ├── test_audit.py           # Audit trail tests
│   └── test_external_apis.py   # API integration tests
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Local development setup
├── Dockerfile                  # Production container
└── README.md                   # Setup and usage documentation
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Use Decimal for all money calculations - float causes rounding errors
# CRITICAL: SQLAlchemy temporal tables require careful transaction handling
# CRITICAL: Google Maps API has 2500 requests/day free tier limit
# CRITICAL: QuickBooks API requires OAuth2 refresh token rotation
# CRITICAL: JWT tokens must include role for permission checking
# CRITICAL: Offline mode requires IndexedDB for local storage
# CRITICAL: PostgreSQL advisory locks needed for concurrent calculations
# CRITICAL: Fuel price APIs often have aggressive rate limits (100/hour)
# CRITICAL: Equipment availability must check maintenance schedules
# CRITICAL: Multi-location rates require timezone-aware calculations
```

## Implementation Blueprint

### Data models and structure

```python
# Base model with audit fields (models/base.py)
from sqlalchemy import Column, DateTime, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)  # User ID
    updated_by = Column(String)  # User ID
    
    # For soft deletes
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String, nullable=True)

# User roles enum (models/user.py)
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"          # Full access to all features and costs
    MANAGER = "manager"      # Approve quotes, view costs
    ESTIMATOR = "estimator"  # Create quotes, limited cost visibility
    VIEWER = "viewer"        # Read-only access

# Cost model with effective dating (models/costs.py)
class LaborRate(BaseModel):
    __tablename__ = "labor_rates"
    
    role = Column(String, nullable=False)  # e.g., "climber", "groundsman"
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    overtime_multiplier = Column(Numeric(3, 2), default=1.5)
    
    # Effective dating
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    
    # Ensure no overlapping date ranges
    __table_args__ = (
        Index('idx_labor_rate_effective', 'role', 'effective_from', 'effective_to'),
        CheckConstraint('effective_to IS NULL OR effective_to > effective_from'),
    )

# Calculation schema with validation (schemas/calculation.py)
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from typing import List, Optional

class CalculationInput(BaseModel):
    # Travel inputs
    travel_miles: Decimal = Field(..., ge=0, decimal_places=1)
    travel_time_minutes: int = Field(..., ge=0)
    
    # Labor inputs
    crew_size: int = Field(..., ge=1, le=10)
    estimated_hours: Decimal = Field(..., ge=0.5, decimal_places=1)
    labor_rates: List[str] = Field(..., min_items=1)  # Role names
    
    # Equipment
    equipment_ids: List[int] = Field(default=[])
    
    # Job specifics
    disposal_fees: Decimal = Field(0, ge=0, decimal_places=2)
    permit_cost: Decimal = Field(0, ge=0, decimal_places=2)
    
    # Multipliers
    emergency_job: bool = Field(False)
    weekend_work: bool = Field(False)
    
    @validator('travel_miles')
    def validate_reasonable_distance(cls, v):
        if v > 500:
            raise ValueError("Travel distance exceeds reasonable limit")
        return v
    
    @validator('estimated_hours')
    def validate_reasonable_hours(cls, v):
        if v > 16:
            raise ValueError("Single day work cannot exceed 16 hours")
        return v

class CalculationResult(BaseModel):
    # Breakdown of costs
    travel_cost: Decimal = Field(..., decimal_places=2)
    labor_cost: Decimal = Field(..., decimal_places=2)
    equipment_cost: Decimal = Field(..., decimal_places=2)
    overhead_cost: Decimal = Field(..., decimal_places=2)
    variable_extras: Decimal = Field(..., decimal_places=2)
    
    # Margins
    safety_buffer: Decimal = Field(..., decimal_places=2)
    profit_margin: Decimal = Field(..., decimal_places=2)
    
    # Final
    subtotal: Decimal = Field(..., decimal_places=2)
    final_total: Decimal = Field(..., decimal_places=2)  # Rounded to $5
    
    # Audit trail
    calculation_id: str = Field(..., description="UUID for audit trail")
    formula_version: str = Field("1.0")
    calculated_at: datetime
    
    class Config:
        json_encoders = {
            Decimal: str  # Serialize Decimal as string to preserve precision
        }
```

### List of tasks to be completed

```yaml
Task 1: Setup Project Structure and Configuration
CREATE src/core/config.py:
  - Use pydantic-settings for environment management
  - Include database URL, JWT settings, API keys
  - Implement settings validation

CREATE docker-compose.yml:
  - PostgreSQL with proper initialization
  - Redis for caching
  - Environment variable configuration

CREATE alembic.ini and initial migration:
  - Configure Alembic for database migrations
  - Create initial schema with audit tables

Task 2: Implement Base Models with Audit Trail
CREATE src/models/base.py:
  - BaseModel with audit fields
  - Soft delete functionality
  - Automatic audit trail tracking

CREATE src/models/audit.py:
  - AuditLog model for change tracking
  - JSON field for before/after values
  - Indexed by entity and timestamp

Task 3: Implement Authentication and Authorization
CREATE src/core/security.py:
  - JWT token generation and validation
  - Password hashing with bcrypt
  - Role-based permission decorators

CREATE src/api/auth.py:
  - Login endpoint with JWT response
  - Token refresh endpoint
  - Role validation middleware

Task 4: Create Cost Management System
CREATE src/models/costs.py:
  - Labor rates with effective dating
  - Equipment costs with availability
  - Overhead calculation rules
  - Temporal table patterns

CREATE src/api/costs.py:
  - CRUD endpoints for cost management
  - Admin-only access
  - Effective date validation

Task 5: Implement Deterministic Calculator Engine
CREATE src/core/calculator.py:
  - PATTERN: Pure functions for each calculation step
  - Decimal precision throughout
  - Deterministic formula pipeline
  - Audit trail generation

CREATE src/services/calculation.py:
  - Business logic orchestration
  - External API integration points
  - Caching layer for repeated calculations

Task 6: Build Estimate Management
CREATE src/models/estimate.py:
  - Estimate model with status workflow
  - Link to calculations and audit trail
  - Customer information

CREATE src/api/estimates.py:
  - CRUD endpoints for estimates
  - Real-time calculation updates
  - PDF generation endpoint

Task 7: Integrate External APIs
CREATE src/services/external_apis.py:
  - Google Maps distance matrix integration
  - QuickBooks invoice creation
  - Fuel price API with caching
  - Rate limit handling and retries

Task 8: Add Comprehensive Testing
CREATE tests/:
  - Unit tests for calculator engine
  - Integration tests for API endpoints
  - Mock external API responses
  - Test audit trail accuracy
  - Performance tests for calculations

Task 9: Create Database Indexes and Optimization
CREATE alembic migration:
  - Indexes for audit queries
  - Effective date range indexes
  - Performance optimization
  - Materialized views for reports

Task 10: Implement Reporting and Analytics
CREATE src/api/reports.py:
  - Historical accuracy reports
  - Cost trend analysis
  - User activity reports
  - Export to CSV/Excel

Task 11: Add Frontend Integration Points
CREATE src/api/websocket.py:
  - Real-time calculation updates
  - Collaborative editing support
  - Offline sync endpoints

Task 12: Production Readiness
CREATE deployment configuration:
  - Health check endpoints
  - Prometheus metrics
  - Structured logging
  - Backup and recovery procedures
```

### Per task pseudocode

```python
# Task 5: Deterministic Calculator Engine
# src/core/calculator.py
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List
import uuid
from datetime import datetime

class DeterministicCalculator:
    """Pure functional calculator with deterministic output"""
    
    @staticmethod
    def calculate_travel_cost(
        miles: Decimal, 
        time_minutes: int,
        vehicle_rate_per_mile: Decimal,
        driver_hourly_rate: Decimal
    ) -> Dict[str, Decimal]:
        # PATTERN: All calculations use Decimal for precision
        mileage_cost = miles * vehicle_rate_per_mile
        time_hours = Decimal(time_minutes) / Decimal(60)
        time_cost = time_hours * driver_hourly_rate
        
        return {
            "mileage_cost": mileage_cost.quantize(Decimal('0.01')),
            "time_cost": time_cost.quantize(Decimal('0.01')),
            "total": (mileage_cost + time_cost).quantize(Decimal('0.01'))
        }
    
    @staticmethod
    def calculate_labor_cost(
        hours: Decimal,
        crew: List[Dict[str, Decimal]],
        multipliers: Dict[str, Decimal]
    ) -> Dict[str, Decimal]:
        # CRITICAL: Apply multipliers in consistent order
        base_cost = sum(
            hours * worker['hourly_rate'] 
            for worker in crew
        )
        
        # Apply multipliers in deterministic order
        total = base_cost
        for key in sorted(multipliers.keys()):  # Sort for consistency
            total *= multipliers[key]
        
        return {
            "base_cost": base_cost.quantize(Decimal('0.01')),
            "multipliers_applied": multipliers,
            "total": total.quantize(Decimal('0.01'))
        }
    
    @staticmethod
    def apply_formula_pipeline(
        components: Dict[str, Decimal],
        overhead_percent: Decimal,
        profit_percent: Decimal,
        safety_buffer_percent: Decimal
    ) -> Dict[str, Decimal]:
        # PATTERN: Deterministic pipeline order
        # 1. Sum all direct costs
        direct_costs = sum(components.values())
        
        # 2. Apply overhead
        overhead = direct_costs * (overhead_percent / Decimal(100))
        subtotal_with_overhead = direct_costs + overhead
        
        # 3. Apply safety buffer
        safety_buffer = subtotal_with_overhead * (safety_buffer_percent / Decimal(100))
        subtotal_with_buffer = subtotal_with_overhead + safety_buffer
        
        # 4. Apply profit margin
        profit = subtotal_with_buffer * (profit_percent / Decimal(100))
        final_subtotal = subtotal_with_buffer + profit
        
        # 5. Round to nearest $5
        final_total = (final_subtotal / Decimal(5)).quantize(
            Decimal('1'), rounding=ROUND_HALF_UP
        ) * Decimal(5)
        
        return {
            "direct_costs": direct_costs.quantize(Decimal('0.01')),
            "overhead": overhead.quantize(Decimal('0.01')),
            "safety_buffer": safety_buffer.quantize(Decimal('0.01')),
            "profit": profit.quantize(Decimal('0.01')),
            "subtotal": final_subtotal.quantize(Decimal('0.01')),
            "final_total": final_total,
            "calculation_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow()
        }

# Task 7: External API Integration with rate limiting
# src/services/external_apis.py
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from functools import lru_cache
from datetime import datetime, timedelta

class ExternalAPIService:
    def __init__(self, config: Settings):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_travel_distance(
        self, 
        origin: str, 
        destination: str
    ) -> Dict[str, Any]:
        # PATTERN: Cache results for 24 hours
        cache_key = f"distance:{origin}:{destination}"
        cached = await self.get_from_cache(cache_key)
        if cached:
            return cached
            
        # GOTCHA: Google Maps has daily quota
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": origin,
            "destinations": destination,
            "key": self.config.GOOGLE_MAPS_API_KEY,
            "units": "imperial"
        }
        
        response = await self.client.get(url, params=params)
        if response.status_code == 429:  # Rate limited
            raise RateLimitError("Google Maps API rate limit exceeded")
            
        data = response.json()
        result = {
            "distance_miles": data['rows'][0]['elements'][0]['distance']['value'] / 1609.34,
            "duration_minutes": data['rows'][0]['elements'][0]['duration']['value'] / 60
        }
        
        await self.set_cache(cache_key, result, ttl=86400)  # 24 hours
        return result
    
    async def create_quickbooks_invoice(
        self,
        estimate: Estimate,
        auth_token: str
    ) -> str:
        # CRITICAL: QuickBooks requires token refresh
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # PATTERN: Map estimate to QuickBooks format
        invoice_data = {
            "CustomerRef": {"value": estimate.customer_id},
            "Line": [
                {
                    "Amount": str(estimate.final_total),
                    "DetailType": "SalesItemLineDetail",
                    "SalesItemLineDetail": {
                        "ItemRef": {"value": "1"}  # Service item
                    },
                    "Description": estimate.description
                }
            ]
        }
        
        url = f"{self.config.QUICKBOOKS_API_URL}/v3/company/{self.config.QB_COMPANY_ID}/invoice"
        response = await self.client.post(url, json=invoice_data, headers=headers)
        
        if response.status_code == 401:
            # Token expired, need refresh
            raise TokenExpiredError("QuickBooks token needs refresh")
            
        return response.json()["Invoice"]["Id"]
```

### Integration Points
```yaml
DATABASE:
  - PostgreSQL 14+ for temporal table support
  - Enable pgcrypto extension for UUID generation
  - Create indexes for effective date queries
  - Set up logical replication for audit tables
  
ENVIRONMENT:
  - add to: .env
  - vars: |
      # Database
      DATABASE_URL=postgresql://user:pass@localhost/treeservice
      
      # Security
      SECRET_KEY=your-secret-key-here
      ALGORITHM=HS256
      ACCESS_TOKEN_EXPIRE_MINUTES=30
      
      # External APIs
      GOOGLE_MAPS_API_KEY=AIza...
      QUICKBOOKS_CLIENT_ID=AB...
      QUICKBOOKS_CLIENT_SECRET=...
      FUEL_API_KEY=...
      
      # Redis Cache
      REDIS_URL=redis://localhost:6379/0
      
      # Business Rules
      DEFAULT_OVERHEAD_PERCENT=25.0
      DEFAULT_PROFIT_PERCENT=35.0
      DEFAULT_SAFETY_BUFFER_PERCENT=10.0
      
DEPENDENCIES:
  - FastAPI[all] for web framework
  - SQLAlchemy 2.0+ for ORM
  - alembic for migrations
  - pydantic[email] for validation
  - python-jose[cryptography] for JWT
  - passlib[bcrypt] for passwords
  - httpx for async HTTP
  - redis for caching
  - celery for background tasks
  - pytest-asyncio for testing
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Setup virtual environment first
python -m venv venv_linux
source venv_linux/bin/activate  # On Windows: venv_linux\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run these FIRST - fix any errors before proceeding
ruff check src/ tests/ --fix    # Auto-fix style issues
mypy src/                        # Type checking
black src/ tests/                # Format code

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Unit Tests
```python
# test_calculator.py - Critical calculation tests
import pytest
from decimal import Decimal
from src.core.calculator import DeterministicCalculator

def test_travel_cost_calculation():
    """Test accurate travel cost calculation"""
    result = DeterministicCalculator.calculate_travel_cost(
        miles=Decimal('50.5'),
        time_minutes=45,
        vehicle_rate_per_mile=Decimal('0.65'),
        driver_hourly_rate=Decimal('25.00')
    )
    
    assert result['mileage_cost'] == Decimal('32.83')  # 50.5 * 0.65
    assert result['time_cost'] == Decimal('18.75')     # 45/60 * 25
    assert result['total'] == Decimal('51.58')

def test_formula_pipeline_deterministic():
    """Test formula pipeline produces consistent results"""
    components = {
        'labor': Decimal('500.00'),
        'equipment': Decimal('200.00'),
        'travel': Decimal('50.00')
    }
    
    result1 = DeterministicCalculator.apply_formula_pipeline(
        components=components,
        overhead_percent=Decimal('25'),
        profit_percent=Decimal('35'),
        safety_buffer_percent=Decimal('10')
    )
    
    result2 = DeterministicCalculator.apply_formula_pipeline(
        components=components,
        overhead_percent=Decimal('25'),
        profit_percent=Decimal('35'),
        safety_buffer_percent=Decimal('10')
    )
    
    # Must be exactly equal
    assert result1 == result2
    assert result1['calculation_id'] != result2['calculation_id']  # Different IDs
    
def test_final_total_rounds_to_five():
    """Test final total rounds to nearest $5"""
    test_cases = [
        (Decimal('1232.50'), Decimal('1235')),  # Round up
        (Decimal('1232.49'), Decimal('1230')),  # Round down
        (Decimal('1235.00'), Decimal('1235')),  # Already rounded
    ]
    
    for subtotal, expected in test_cases:
        result = DeterministicCalculator.round_to_nearest_five(subtotal)
        assert result == expected

# test_auth.py - Role-based access tests
@pytest.mark.asyncio
async def test_role_permissions():
    """Test role-based access control"""
    from src.api.deps import check_permission
    
    # Admin can access everything
    admin_user = User(role=UserRole.ADMIN)
    assert await check_permission(admin_user, "costs:write") == True
    
    # Estimator cannot modify costs
    estimator_user = User(role=UserRole.ESTIMATOR)
    assert await check_permission(estimator_user, "costs:write") == False
    assert await check_permission(estimator_user, "estimates:create") == True
    
    # Viewer is read-only
    viewer_user = User(role=UserRole.VIEWER)
    assert await check_permission(viewer_user, "estimates:create") == False
    assert await check_permission(viewer_user, "estimates:read") == True

# test_audit.py - Audit trail tests
@pytest.mark.asyncio
async def test_audit_trail_creation():
    """Test audit trail captures all changes"""
    from src.services.audit import AuditService
    
    # Create estimate
    estimate = await create_estimate(...)
    
    # Check audit log
    audit_logs = await AuditService.get_logs_for_entity(
        entity_type="estimate",
        entity_id=estimate.id
    )
    
    assert len(audit_logs) == 1
    assert audit_logs[0].action == "CREATE"
    assert audit_logs[0].user_id == current_user.id
    assert audit_logs[0].changes["after"]["status"] == "draft"
```

```bash
# Run tests iteratively until passing:
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file during development:
pytest tests/test_calculator.py -v -s

# If failing: Debug specific test, fix code, re-run
```

### Level 3: Integration Tests
```bash
# Start services
docker-compose up -d

# Run database migrations
alembic upgrade head

# Start the application
uvicorn src.main:app --reload

# Test authentication
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Expected: {"access_token": "...", "token_type": "bearer"}

# Test estimate creation (use token from above)
curl -X POST http://localhost:8000/api/estimates/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Doe",
    "travel_miles": 25.5,
    "travel_time_minutes": 30,
    "crew_size": 3,
    "estimated_hours": 4.5,
    "labor_rates": ["climber", "groundsman", "groundsman"],
    "equipment_ids": [1, 3],
    "disposal_fees": 150.00
  }'

# Expected: Full calculation breakdown with final total rounded to $5

# Test real-time updates via WebSocket
wscat -c ws://localhost:8000/ws/estimates/123 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Level 4: Performance Tests
```python
# test_performance.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.asyncio
async def test_calculation_performance():
    """Test calculations complete within 100ms"""
    start = time.time()
    
    result = await calculation_service.calculate(
        CalculationInput(...)
    )
    
    duration = (time.time() - start) * 1000  # Convert to ms
    assert duration < 100, f"Calculation took {duration}ms"

@pytest.mark.asyncio
async def test_concurrent_calculations():
    """Test system handles concurrent calculations"""
    inputs = [generate_random_input() for _ in range(100)]
    
    # Run 100 calculations concurrently
    tasks = [
        calculation_service.calculate(input_data)
        for input_data in inputs
    ]
    
    results = await asyncio.gather(*tasks)
    
    # All should succeed
    assert len(results) == 100
    assert all(r.final_total > 0 for r in results)
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check src/`
- [ ] No type errors: `mypy src/`
- [ ] API documentation generated: http://localhost:8000/docs
- [ ] Role-based permissions work correctly
- [ ] Calculations are deterministic (same input = same output)
- [ ] Audit trail captures all changes
- [ ] External API integrations handle failures gracefully
- [ ] Performance targets met (<100ms calculations)
- [ ] Mobile responsive UI works offline
- [ ] Database indexes optimize query performance
- [ ] 7-year data retention policy implemented
- [ ] Backup and recovery procedures documented

---

## Anti-Patterns to Avoid
- ❌ Don't use float for money - always use Decimal
- ❌ Don't calculate in parallel - maintain deterministic order
- ❌ Don't skip effective date validation
- ❌ Don't expose internal costs to unauthorized users
- ❌ Don't ignore API rate limits
- ❌ Don't forget audit trail for sensitive changes
- ❌ Don't hardcode business rules - use configuration
- ❌ Don't cache user-specific calculations
- ❌ Don't allow SQL injection in reports
- ❌ Don't skip timezone handling for multi-location

## Edge Cases to Handle
- Emergency jobs with overtime multipliers
- Seasonal cost variations (winter rates)
- Multi-location rate differences
- Equipment unavailable due to maintenance
- Partial day calculations
- Travel across state lines (different tax rates)
- Customers with negotiated rates
- Historical quote recreation with deleted cost records
- Concurrent estimate updates
- Offline mode data conflicts

## Performance Optimization Tips
- Use PostgreSQL materialized views for reports
- Cache external API responses aggressively
- Implement database connection pooling
- Use Redis for session management
- Batch audit log inserts
- Optimize indexes for effective date queries
- Use EXPLAIN ANALYZE for slow queries
- Implement read replicas for reporting

## Security Considerations
- JWT tokens must expire and refresh
- Rate limit all API endpoints
- Sanitize all user inputs
- Use prepared statements for all queries
- Encrypt sensitive data at rest
- Implement CORS properly
- Log all permission denials
- Regular security dependency updates
- Implement API key rotation
- Monitor for suspicious patterns

## Monitoring and Observability
- Structured logging with correlation IDs
- Prometheus metrics for all endpoints
- Alert on calculation accuracy deviation
- Track API integration success rates
- Monitor database query performance
- Log all audit trail queries
- Track user session analytics
- Monitor background job queues
- Set up uptime monitoring
- Dashboard for business metrics

## Confidence Score: 9/10

High confidence due to:
- Clear requirements with specific formula pipeline
- Well-established patterns for FastAPI + PostgreSQL
- Comprehensive audit trail requirements addressed
- Role-based permissions clearly defined
- External API documentation available
- Validation gates cover all critical paths

Minor uncertainty on:
- Exact QuickBooks API field mappings (but documentation available)
- Offline sync conflict resolution strategy (but patterns exist)

The implementation plan is comprehensive with clear patterns to follow, proper error handling, and extensive validation gates to ensure one-pass success.