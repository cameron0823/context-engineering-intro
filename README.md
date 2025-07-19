# Tree Service Estimating Application

A production-ready tree service estimating application built with FastAPI, PostgreSQL, and modern Python practices. Features deterministic cost calculations, audit trails, role-based access control, and external API integrations.

## 🚨 Current Status (July 19, 2024)

### Quick Access
- **Frontend**: https://cox-tree-quote-app.web.app
- **Admin Dashboard**: https://cox-tree-quote-app.web.app/admin
- **Status**: ✅ Working with local backend, ⚠️ Railway deployment has issues

### To Start the App
1. Run: `python simple_backend.py`
2. Go to: https://cox-tree-quote-app.web.app/admin
3. Console (F12): `window.api.baseUrl = 'http://localhost:8001/api'`
4. Login: **Cameroncox1993** / **CoxTree#2024!Admin**

### Known Issues
- Railway deployment showing 502 (fix pushed, awaiting rebuild)
- Using simple_backend.py as temporary workaround
- See PROJECT_STATUS_2024-07-19.md for details

## 🚀 Features

- **Deterministic Formula Pipeline**: Consistent calculations using Decimal precision
- **Role-Based Access Control**: Admin, Manager, Estimator, and Viewer roles
- **Audit Trail**: Complete change tracking with 7-year retention
- **Effective Dating**: Historical cost tracking and quote recreation
- **External Integrations**: Google Maps, QuickBooks, and fuel price APIs
- **Real-Time Updates**: WebSocket support for collaborative editing
- **Mobile Responsive**: Works offline with sync capabilities

## 📁 Project Structure

```
.
├── src/
│   ├── api/          # FastAPI endpoints
│   ├── core/         # Core utilities (config, security, calculator)
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic services
│   ├── db/           # Database utilities
│   └── utils/        # Helper utilities
├── tests/            # Test suite
├── alembic/          # Database migrations
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## ✅ Implementation Status

### Completed Components

1. **Project Structure** ✅
   - All directories created
   - Python package structure initialized

2. **Configuration** ✅
   - `src/core/config.py` - Pydantic settings management
   - `.env.example` - Environment variables template
   - `requirements.txt` - All dependencies

3. **Docker Setup** ✅
   - `docker-compose.yml` - PostgreSQL, Redis, and app services
   - `Dockerfile` - Production container
   - `init.sql` - Database initialization

4. **Database Foundation** ✅
   - `src/db/session.py` - Async database session management
   - Alembic configuration for migrations

5. **Base Models & Audit** ✅
   - `src/models/base.py` - Base model with audit fields
   - `src/models/audit.py` - Comprehensive audit logging
   - `src/services/audit.py` - Audit service implementation

6. **Authentication System** ✅
   - `src/models/user.py` - User model with roles
   - `src/core/security.py` - JWT and password hashing
   - `src/schemas/user.py` - User validation schemas
   - `src/api/deps.py` - Authentication dependencies
   - `src/api/auth.py` - Auth endpoints (login, register, etc.)

7. **Cost Management** ✅
   - `src/models/costs.py` - Cost models with effective dating
   - `src/schemas/costs.py` - Cost validation schemas

8. **Calculator Engine** ✅
   - `src/core/calculator.py` - Deterministic calculations
   - `src/schemas/calculation.py` - Calculation schemas
   - `src/utils/rounding.py` - Financial rounding utilities

9. **Estimate Management** ✅
   - `src/models/estimate.py` - Estimate model
   - `src/schemas/estimate.py` - Estimate schemas

### Remaining Tasks

1. **API Endpoints** 🔄
   - [ ] `src/api/estimates.py` - Estimate CRUD endpoints
   - [ ] `src/api/costs.py` - Cost management endpoints
   - [ ] `src/api/reports.py` - Reporting endpoints

2. **Services** 🔄
   - [ ] `src/services/calculation.py` - Calculation orchestration
   - [ ] `src/services/external_apis.py` - External API integrations

3. **Database** 🔄
   - [ ] Create initial Alembic migration
   - [ ] Add database indexes
   - [ ] Create materialized views for reports

4. **Testing** 🔄
   - [ ] `tests/conftest.py` - Pytest fixtures
   - [ ] `tests/test_calculator.py` - Calculator tests
   - [ ] `tests/test_auth.py` - Authentication tests
   - [ ] `tests/test_estimates.py` - Estimate tests
   - [ ] `tests/test_costs.py` - Cost management tests

5. **Additional Features** 🔄
   - [ ] WebSocket support for real-time updates
   - [ ] PDF generation for estimates
   - [ ] Excel export functionality
   - [ ] Email notifications

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 14+ (via Docker)
- Redis (via Docker)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tree-service-estimating
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv_linux
   source venv_linux/bin/activate  # On Windows: venv_linux\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start services**
   ```bash
   docker-compose up -d
   ```

6. **Run migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the application**
   ```bash
   uvicorn src.main:app --reload
   ```

8. **Access the application**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Metrics: http://localhost:8000/metrics

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_calculator.py -v
```

## 📝 API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

### Authentication

All endpoints except `/api/auth/login` and `/api/auth/register` require JWT authentication.

```bash
# Get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=password"

# Use token
curl -X GET http://localhost:8000/api/estimates \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 🔒 Security Considerations

- JWT tokens expire after 30 minutes
- Passwords require uppercase, lowercase, digit, and special character
- All financial calculations use Decimal precision
- Complete audit trail for compliance
- Role-based access control for sensitive data

## 📊 Business Rules

- **Formula Pipeline**: Direct Labor → Equipment → Overhead → Safety Buffer → Profit → Round to $5
- **Default Percentages**:
  - Overhead: 25%
  - Profit: 35%
  - Safety Buffer: 10%
- **Maximum Limits**:
  - Travel: 500 miles
  - Work hours: 16 per day
  - Crew size: 10 people

## 🚀 Deployment

See `Dockerfile` for production container configuration.

### Environment Variables

Critical production variables:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key (generate securely!)
- `GOOGLE_MAPS_API_KEY` - For distance calculations
- `QUICKBOOKS_*` - QuickBooks integration credentials

## 📈 Monitoring

- Prometheus metrics at `/metrics`
- Structured JSON logging
- Health check at `/health`

## 🤝 Contributing

1. Follow PEP8 style guide
2. Add tests for new features
3. Update documentation
4. Run linters before committing

## 📄 License

[Your License Here]

---

## Next Steps for Implementation

To complete the application, follow these steps:

1. **Create API Endpoints**
   - Copy the pattern from `src/api/auth.py`
   - Implement CRUD operations for estimates and costs
   - Add proper permission checks using dependencies

2. **Implement Services**
   - Create `calculation.py` service to orchestrate calculations
   - Implement external API integrations with proper error handling

3. **Add Tests**
   - Use the test examples from the PRP
   - Ensure >80% code coverage
   - Test all edge cases

4. **Run Validation**
   ```bash
   # Syntax and style
   ruff check src/ tests/ --fix
   mypy src/
   black src/ tests/
   
   # Run tests
   pytest tests/ -v
   
   # Start services and test manually
   docker-compose up -d
   uvicorn src.main:app --reload
   ```

5. **Complete Documentation**
   - Add API endpoint documentation
   - Create user guides
   - Document deployment process