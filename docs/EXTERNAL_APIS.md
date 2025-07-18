# External API Integrations

This document describes the external API integrations implemented in the Tree Service Estimating application.

## Overview

The application integrates with three external services:
1. **Google Maps Distance Matrix API** - For accurate travel distance and time calculations
2. **QuickBooks API** - For creating invoices from approved estimates
3. **Fuel Price API** - For current fuel price data (currently using mock data)

## Architecture

### Service Layer (`src/services/external_apis.py`)

The `ExternalAPIService` class provides a unified interface for all external API interactions:

- **Caching**: All API responses are cached to reduce API calls and costs
- **Error Handling**: Comprehensive error handling with custom exception types
- **Retry Logic**: Automatic retries with exponential backoff for transient failures
- **Rate Limiting**: Respects API rate limits configured in settings

### Cache Layer (`src/core/cache.py`)

The caching system provides:
- **Redis Support**: Primary cache using Redis for distributed caching
- **In-Memory Fallback**: Automatic fallback to in-memory cache if Redis is unavailable
- **TTL Management**: Configurable time-to-live for different data types

## Google Maps Integration

### Configuration
```env
GOOGLE_MAPS_API_KEY=your-api-key-here
GOOGLE_MAPS_DAILY_LIMIT=2500
```

### Usage

#### Calculate Distance Between Two Addresses
```python
POST /api/external/distance
{
    "origin": "123 Main St, Anytown, USA",
    "destination": "456 Oak Ave, Somewhere, USA",
    "departure_time": "2024-01-17T10:00:00"  // Optional, for traffic
}

Response:
{
    "origin": "123 Main St, Anytown, USA",
    "destination": "456 Oak Ave, Somewhere, USA",
    "distance_miles": 15.2,
    "duration_minutes": 25,
    "distance_text": "15.2 mi",
    "duration_text": "25 mins",
    "calculated_at": "2024-01-17T09:30:00"
}
```

#### Batch Distance Calculation
```python
POST /api/external/distance/batch
{
    "origin": "Company HQ",
    "destinations": [
        "Customer 1 Address",
        "Customer 2 Address",
        "Customer 3 Address"
    ]
}
```

### Integration with Estimates

The calculation service can optionally use Google Maps for accurate distance:

```python
# In the estimate creation process
calculation_service = CalculationService(db)
result = await calculation_service.calculate_estimate(
    calculation_input=input_data,
    use_google_maps=True,
    origin_address="Company HQ",
    destination_address=estimate.job_address
)
```

## QuickBooks Integration

### Configuration
```env
QUICKBOOKS_CLIENT_ID=your-client-id
QUICKBOOKS_CLIENT_SECRET=your-client-secret
QUICKBOOKS_COMPANY_ID=your-company-id
QUICKBOOKS_API_URL=https://sandbox-quickbooks.api.intuit.com  # or production URL
```

### OAuth Setup (Not Implemented)
The current implementation has a placeholder for OAuth token management. In production, you'll need to:
1. Implement OAuth2 flow for QuickBooks authorization
2. Store and refresh tokens securely
3. Handle token expiration and renewal

### Usage

#### Create Invoice from Estimate
```python
POST /api/estimates/{estimate_id}/create-invoice

Response:
{
    "detail": "QuickBooks invoice created successfully",
    "invoice": {
        "id": "INV-001",
        "number": "1001",
        "url": "https://quickbooks.intuit.com/app/invoice?txnId=INV-001",
        "total": "1500.00",
        "created_at": "2024-01-17T10:00:00"
    }
}
```

### Features
- **Customer Management**: Automatically creates QuickBooks customers if they don't exist
- **Line Item Details**: Includes breakdown of labor, equipment, travel costs
- **Status Tracking**: Updates estimate status to "INVOICED" after successful creation
- **Audit Trail**: Records all invoice creation actions

## Fuel Price API

### Configuration
```env
FUEL_API_KEY=your-api-key
FUEL_API_HOURLY_LIMIT=100
```

### Usage

#### Get Current Fuel Price
```python
GET /api/external/fuel-price?location=local&fuel_type=regular

Response:
{
    "price_per_gallon": "3.50",
    "fuel_type": "regular",
    "location": "local",
    "last_updated": "2024-01-17T10:00:00",
    "source": "mock_api"
}
```

### Note on Implementation
The current implementation uses mock data. To integrate with a real fuel price API:
1. Choose a provider (e.g., GasBuddy API, EIA.gov, or commercial services)
2. Update the `get_current_fuel_price` method in `ExternalAPIService`
3. Implement proper authentication and request formatting

## API Health Monitoring

### Health Check Endpoint
```python
GET /api/external/health

Response:
{
    "status": "healthy",  // or "degraded" if any service is down
    "services": {
        "google_maps": true,
        "quickbooks": true,
        "fuel_api": true
    },
    "checked_at": "2024-01-17T10:00:00"
}
```

## Error Handling

All external API integrations include comprehensive error handling:

- **Network Errors**: Automatic retries with exponential backoff
- **API Errors**: Specific error messages and appropriate HTTP status codes
- **Rate Limiting**: Respects API limits and returns 429 when exceeded
- **Validation Errors**: Input validation before making API calls

### Error Response Format
```json
{
    "detail": "Google Maps API error: Invalid API key"
}
```

## Caching Strategy

Different cache TTLs for different data types:
- **Distance Calculations**: 24 hours (unlikely to change)
- **Fuel Prices**: 4 hours (changes periodically)
- **API Health Status**: Not cached (real-time monitoring)

## Security Considerations

1. **API Keys**: Store in environment variables, never commit to repository
2. **Request Validation**: Validate all inputs before making external API calls
3. **Error Messages**: Don't expose sensitive information in error responses
4. **Rate Limiting**: Implement client-side rate limiting to prevent abuse
5. **HTTPS Only**: All external API calls use HTTPS

## Testing

The test suite (`tests/test_external_apis.py`) includes:
- Unit tests for each API integration
- Mock responses for all external services
- Error handling scenarios
- Cache behavior verification

### Running Tests
```bash
pytest tests/test_external_apis.py -v
```

## Future Enhancements

1. **Real Fuel API Integration**: Replace mock implementation with actual fuel price API
2. **QuickBooks OAuth Flow**: Implement complete OAuth2 authentication
3. **Webhooks**: Add webhook support for QuickBooks invoice updates
4. **Additional APIs**:
   - Weather API for scheduling considerations
   - SMS/Email notification services
   - Payment processing integration
5. **API Analytics**: Track API usage and costs
6. **Circuit Breaker Pattern**: Implement circuit breakers for better fault tolerance