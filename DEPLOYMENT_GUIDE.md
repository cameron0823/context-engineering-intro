# Tree Service Estimating App - Deployment Guide

## 🚀 Quick Start for Team Members

### Prerequisites
- Python 3.11 or higher
- PostgreSQL database
- Redis (for caching)

### Step 1: Clone and Setup
```bash
# Clone the repository
git clone [your-repo-url]
cd tree-service-estimating

# Create virtual environment
python -m venv venv_linux
source venv_linux/bin/activate  # On Windows: venv_linux\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and update:
# - DATABASE_URL (your PostgreSQL connection)
# - SECRET_KEY (generate a secure key)
# - API keys for Google Maps and QuickBooks
```

### Step 3: Database Setup
```bash
# Run database migrations
alembic upgrade head

# Create initial admin user
python scripts/create_test_users.py
```

### Step 4: Start the Application
```bash
# Development mode
uvicorn src.main:app --reload --port 8002

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8002 --workers 4
```

### Step 5: Access the Application
- API Documentation: http://localhost:8002/docs
- Health Check: http://localhost:8002/health

## 👥 User Roles and Permissions

### Admin
- Full access to all features
- Can modify cost settings and overhead percentages
- Can manage users and view all estimates
- Can access detailed cost breakdowns

### Manager
- Can approve and modify estimates
- Can view cost information
- Can generate reports
- Cannot modify system settings

### Estimator
- Can create and edit estimates
- Can view limited cost information
- Can duplicate existing estimates
- Cannot approve estimates or modify costs

### Viewer
- Read-only access to estimates
- Cannot see detailed cost breakdowns
- Cannot create or modify anything

## 🔑 Default Test Accounts

| Role | Username | Password | Email |
|------|----------|----------|--------|
| Admin | admin | Admin123! | admin@treeservice.com |
| Manager | manager | Manager123! | manager@treeservice.com |
| Estimator | estimator | Estimator123! | estimator@treeservice.com |
| Viewer | viewer | Viewer123! | viewer@treeservice.com |

**⚠️ IMPORTANT: Change these passwords immediately in production!**

## 📝 Creating Estimates

### Basic Workflow
1. Login with estimator or higher role
2. Navigate to "Create Estimate"
3. Enter customer information
4. Add travel details (address will auto-calculate distance)
5. Configure crew and hours
6. Add equipment if needed
7. Review calculation
8. Save estimate

### Estimate Status Flow
- **Draft** → Initial creation
- **Pending** → Sent to customer
- **Approved** → Customer accepted
- **Rejected** → Customer declined
- **Invoiced** → Work completed and billed

## 🔧 Configuration

### Business Rules (Configurable by Admin)
- Default Overhead: 25%
- Default Profit Margin: 35%
- Safety Buffer: 10%
- Vehicle Rate: $0.65/mile
- Final total rounds to nearest $5

### API Integrations

#### Google Maps
- Used for distance calculations
- Configure in `.env`: `GOOGLE_MAPS_API_KEY`
- Daily limit: 2,500 requests

#### QuickBooks
- For invoice creation
- Configure OAuth2 credentials in `.env`
- Syncs customers and creates invoices

#### Fuel Price API
- Updates vehicle rates based on current fuel prices
- Refreshes hourly

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Check JWT token expiration (30 minutes)
   - Verify user is active and verified
   - Ensure correct role permissions

2. **Calculation Differences**
   - All calculations use Decimal for precision
   - Results are deterministic (same input = same output)
   - Check for weekend/emergency multipliers

3. **Database Connection**
   - Verify PostgreSQL is running
   - Check DATABASE_URL in .env
   - Ensure migrations are up to date

4. **External API Failures**
   - Check API keys are valid
   - Monitor rate limits
   - Review logs for specific errors

## 📊 Monitoring

### Health Checks
- Endpoint: `/health`
- Checks database connectivity
- Verifies Redis cache
- Returns version information

### Logs
- Location: `logs/` directory
- Format: JSON for production
- Includes request ID for tracing

### Metrics
- Endpoint: `/metrics` (Prometheus format)
- Tracks API response times
- Monitors calculation performance
- Counts external API usage

## 🔒 Security Best Practices

1. **API Keys**
   - Never commit to version control
   - Rotate regularly
   - Use environment variables

2. **Database**
   - Use strong passwords
   - Enable SSL connections
   - Regular backups (7-year retention)

3. **User Management**
   - Enforce strong passwords
   - Regular access reviews
   - Audit trail for all changes

## 📱 Mobile Access

The application is mobile-responsive and works offline:
1. Access via mobile browser
2. Add to home screen for app-like experience
3. Calculations work offline
4. Syncs when connection restored

## 🆘 Support

### For Issues:
1. Check logs for errors
2. Verify configuration
3. Test with sample data
4. Contact admin for help

### Regular Maintenance:
- Database backups: Daily
- Log rotation: Weekly
- Security updates: Monthly
- Performance review: Quarterly

## 🎯 Quick Test

Run the comprehensive test suite:
```bash
python test_comprehensive.py
```

This will verify:
- Authentication is working
- Calculator is accurate
- Estimates can be created
- Permissions are correct
- External APIs are configured
- Sample data is created

---

**Ready to start? Run the app and create your first estimate!**