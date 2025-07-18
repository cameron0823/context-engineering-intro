## FEATURE:

Tree service estimating application that provides accurate, real-time job quotes based on travel time, working time, and comprehensive company costs. Must calculate quotes using deterministic formula pipeline with complete audit trail. Core functionality: Travel time costs + Working time costs + Company running costs + Operating costs + Job-specific costs, all processed through custom pricing matrix with effective dating and role-based permissions.

## EXAMPLES:

examples/agent/database_service.py - for audit logging patterns and data persistence
examples/models/ - for Pydantic validation of complex calculations
examples/tests/ - for comprehensive validation including edge cases
examples/api/ - for role-based endpoint patterns with FastAPI

## DOCUMENTATION:

FastAPI Documentation: https://fastapi.tiangolo.com/ - for API structure and validation
Pydantic Documentation: https://docs.pydantic.dev/latest/ - for data models and validation
QuickBooks API: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/customers - for invoice integration
Google Maps API: https://developers.google.com/maps/documentation/distance-matrix/overview - for travel time calculation
PostgreSQL Audit Patterns: https://www.postgresql.org/docs/current/ddl-system-columns.html - for change tracking

## OTHER CONSIDERATIONS:

Formula Pipeline must be deterministic: Direct Labor → Equipment → Overhead → Variable Extras → Safety Buffer → Profit → Final Total (rounded to nearest $5)
Effective dating for all rates - historical quotes must recreate with period-accurate costs
Role-based permissions: Admin (full cost access), Manager (quote approval), Estimator (creation), Viewer (read-only)
95% accuracy target (estimates within 10% of actual costs), 99.9% uptime during business hours
Real-time recalculation when inputs change, mobile responsive with offline capability
7-year data retention for compliance, complete audit trail for every cost change
Integration gotchas: QuickBooks sync timing, fuel price API rate limits, equipment availability thresholds
Edge cases: Emergency job overtime multipliers, seasonal cost variations, multi-location rate differences