# Invoice OCR Analysis API Documentation

## Overview
The Invoice OCR Analysis API provides RESTful endpoints for analyzing invoices using OCR technology. This API allows your team to integrate invoice analysis capabilities directly into your applications, workflows, and systems.

## Base URL
```
http://your-server:5001/api/v1
```

## Authentication
All API endpoints require authentication using an API key passed in the `X-API-Key` header.

```
X-API-Key: your_api_key_here
```

## Default API Keys
- **Admin**: `admin_api_key_12345`
- **Team1**: `team1_api_key_67890`

## Rate Limits
- **Per Minute**: 60 requests
- **Per Hour**: 1,000 requests  
- **Per Day**: 10,000 requests

## Supported File Formats
- PDF (.pdf)
- Images: PNG, JPG, JPEG, TIFF, TIF, BMP, WebP
- **Maximum File Size**: 16MB

---

## Endpoints

### 1. Health Check
**GET** `/health`

Check API health and status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "1.0.0",
  "service": "Invoice OCR Analysis API"
}
```

---

### 2. Analyze Single Invoice
**POST** `/analyze`

Analyze a single invoice file.

**Headers:**
```
X-API-Key: your_api_key_here
Content-Type: multipart/form-data
```

**Body:**
- `file`: Invoice file (PDF or image)

**cURL Example:**
```bash
curl -X POST "http://your-server:5001/api/v1/analyze" \
  -H "X-API-Key: your_api_key_here" \
  -F "file=@invoice.pdf"
```

**Response (Success):**
```json
{
  "success": true,
  "summary": {
    "total_items": 5,
    "matched_items": 4,
    "match_percentage": 80.0,
    "total_invoice_value": 15000.00,
    "overall_status": "GOOD - 70-89% items matched"
  },
  "tax_summary": {
    "igst_amount": 2700.00,
    "output_igst": 2700.00,
    "gst_rate": 18.0,
    "cgst": 1350.00,
    "sgst": 1350.00,
    "sub_total": 15000.00,
    "total_inc_taxes": 17700.00
  },
  "invoice_items": [
    {
      "material_name": "Cotton Fabric",
      "quantity": 100.0,
      "rate": 150.00,
      "amount": 15000.00,
      "status": "EXACT MATCH",
      "csv_match": {
        "database_name": "Premium Cotton",
        "database_supplier": "Textile Corp",
        "database_price": 150.00,
        "match_method": "EXACT",
        "confidence_score": 100.0
      },
      "price_analysis": {
        "invoice_rate": 150.00,
        "database_price": 150.00,
        "difference": 0.00,
        "difference_percentage": 0.0,
        "price_status": "EXACT MATCH"
      }
    }
  ],
  "extracted_text": "Raw OCR text from invoice...",
  "analysis_timestamp": "2024-01-15T10:30:00",
  "file_processed": "invoice.pdf",
  "api_user": "team1",
  "request_id": "req_1705312200_1234"
}
```

**Response (Error):**
```json
{
  "error": "File type not allowed"
}
```

---

### 3. Batch Analyze Multiple Invoices
**POST** `/batch-analyze`

Analyze multiple invoice files in a single request (max 10 files).

**Headers:**
```
X-API-Key: your_api_key_here
Content-Type: multipart/form-data
```

**Body:**
- `files`: Multiple invoice files

**cURL Example:**
```bash
curl -X POST "http://your-server:5001/api/v1/batch-analyze" \
  -H "X-API-Key: your_api_key_here" \
  -F "files=@invoice1.pdf" \
  -F "files=@invoice2.pdf" \
  -F "files=@invoice3.pdf"
```

**Response:**
```json
{
  "success": true,
  "total_files": 3,
  "successful_analyses": 3,
  "failed_analyses": 0,
  "results": [
    {
      "success": true,
      "summary": {...},
      "filename": "invoice1.pdf"
    }
  ],
  "errors": [],
  "batch_id": "batch_1705312200",
  "api_user": "team1"
}
```

---

### 4. Get API Status
**GET** `/status`

Get current API status and user information.

**Headers:**
```
X-API-Key: your_api_key_here
```

**Response:**
```json
{
  "user": "team1",
  "role": "user",
  "timestamp": "2024-01-15T10:30:00",
  "rate_limits": {
    "REQUESTS_PER_MINUTE": 60,
    "REQUESTS_PER_HOUR": 1000,
    "REQUESTS_PER_DAY": 10000
  },
  "supported_formats": ["pdf", "png", "jpg", "jpeg", "tiff", "tif", "bmp", "webp"],
  "max_file_size_mb": 16.0
}
```

---

### 5. Get Rate Limit Status
**GET** `/rate-limits`

Get current rate limit usage for the authenticated user.

**Headers:**
```
X-API-Key: your_api_key_here
```

**Response:**
```json
{
  "user": "team1",
  "current_usage": {
    "last_minute": 15,
    "last_hour": 45,
    "last_day": 150
  },
  "limits": {
    "REQUESTS_PER_MINUTE": 60,
    "REQUESTS_PER_HOUR": 1000,
    "REQUESTS_PER_DAY": 10000
  },
  "remaining": {
    "last_minute": 45,
    "last_hour": 955,
    "last_day": 9850
  }
}
```

---

### 6. List Users (Admin Only)
**GET** `/users`

List all API users (admin access required).

**Headers:**
```
X-API-Key: admin_api_key_here
```

**Response:**
```json
{
  "users": [
    {
      "username": "admin",
      "role": "admin",
      "api_key": "admin_api..."
    },
    {
      "username": "team1",
      "role": "user",
      "api_key": "team1_api..."
    }
  ],
  "total_users": 2
}
```

---

### 7. Create User (Admin Only)
**POST** `/users`

Create a new API user (admin access required).

**Headers:**
```
X-API-Key: admin_api_key_here
Content-Type: application/json
```

**Body:**
```json
{
  "username": "team2",
  "password": "secure_password",
  "role": "user"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User team2 created successfully",
  "api_key": "team2_api_key_1705312200"
}
```

---

## Response Status Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 201  | Created |
| 400  | Bad Request |
| 401  | Unauthorized (Invalid/Missing API Key) |
| 403  | Forbidden (Insufficient Permissions) |
| 404  | Not Found |
| 405  | Method Not Allowed |
| 429  | Rate Limit Exceeded |
| 500  | Internal Server Error |

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error description message"
}
```

For debugging purposes, some errors may include additional details:

```json
{
  "error": "Processing failed: Invalid file format",
  "traceback": "Detailed error traceback..."
}
```

---

## Integration Examples

### Python Integration
```python
import requests

# API Configuration
API_BASE_URL = "http://your-server:5001/api/v1"
API_KEY = "your_api_key_here"

headers = {
    "X-API-Key": API_KEY
}

# Analyze single invoice
def analyze_invoice(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            headers=headers,
            files=files
        )
        return response.json()

# Batch analyze
def batch_analyze(file_paths):
    files = [('files', open(path, 'rb')) for path in file_paths]
    response = requests.post(
        f"{API_BASE_URL}/batch-analyze",
        headers=headers,
        files=files
    )
    return response.json()

# Get status
def get_status():
    response = requests.get(
        f"{API_BASE_URL}/status",
        headers=headers
    )
    return response.json()
```

### JavaScript/Node.js Integration
```javascript
const FormData = require('form-data');
const fs = require('fs');

// API Configuration
const API_BASE_URL = "http://your-server:5001/api/v1";
const API_KEY = "your_api_key_here";

const headers = {
    "X-API-Key": API_KEY
};

// Analyze single invoice
async function analyzeInvoice(filePath) {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    
    const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
            ...headers,
            ...form.getHeaders()
        },
        body: form
    });
    
    return response.json();
}

// Batch analyze
async function batchAnalyze(filePaths) {
    const form = new FormData();
    filePaths.forEach(path => {
        form.append('files', fs.createReadStream(path));
    });
    
    const response = await fetch(`${API_BASE_URL}/batch-analyze`, {
        method: 'POST',
        headers: {
            ...headers,
            ...form.getHeaders()
        },
        body: form
    });
    
    return response.json();
}
```

### cURL Examples

#### Health Check
```bash
curl -X GET "http://your-server:5001/api/v1/health"
```

#### Analyze Invoice
```bash
curl -X POST "http://your-server:5001/api/v1/analyze" \
  -H "X-API-Key: your_api_key_here" \
  -F "file=@invoice.pdf"
```

#### Batch Analyze
```bash
curl -X POST "http://your-server:5001/api/v1/batch-analyze" \
  -H "X-API-Key: your_api_key_here" \
  -F "files=@invoice1.pdf" \
  -F "files=@invoice2.pdf"
```

#### Get Status
```bash
curl -X GET "http://your-server:5001/api/v1/status" \
  -H "X-API-Key: your_api_key_here"
```

---

## Data Models

### Invoice Item
```json
{
  "material_name": "string",
  "quantity": "number",
  "rate": "number",
  "amount": "number",
  "status": "string",
  "csv_match": {
    "database_name": "string",
    "database_supplier": "string",
    "database_price": "number",
    "match_method": "string",
    "confidence_score": "number"
  },
  "price_analysis": {
    "invoice_rate": "number",
    "database_price": "number",
    "difference": "number",
    "difference_percentage": "number",
    "price_status": "string"
  }
}
```

### Summary
```json
{
  "total_items": "number",
  "matched_items": "number",
  "match_percentage": "number",
  "total_invoice_value": "number",
  "overall_status": "string"
}
```

### Tax Summary
```json
{
  "igst_amount": "number",
  "output_igst": "number",
  "gst_rate": "number",
  "cgst": "number",
  "sgst": "number",
  "sub_total": "number",
  "total_inc_taxes": "number"
}
```

---

## Best Practices

1. **Rate Limiting**: Monitor your rate limit usage and implement exponential backoff for retries
2. **Error Handling**: Always check response status codes and handle errors gracefully
3. **File Validation**: Validate file types and sizes before uploading
4. **Batch Processing**: Use batch endpoints for multiple files to reduce API calls
5. **API Key Security**: Keep your API keys secure and rotate them regularly
6. **Monitoring**: Monitor API response times and success rates

---

## Support

For technical support or questions about the API:
- Check the health endpoint for service status
- Review rate limit usage if experiencing 429 errors
- Ensure proper authentication headers are included
- Verify file formats and sizes meet requirements

---

## Changelog

### Version 1.0.0
- Initial API release
- Single and batch invoice analysis
- User management and authentication
- Rate limiting and monitoring
- Comprehensive error handling
