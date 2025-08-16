# Invoice OCR Analysis API

## 🚀 Overview

The Invoice OCR Analysis API provides a robust, production-ready RESTful interface for analyzing invoices using advanced OCR technology. This API allows your team to integrate invoice analysis capabilities directly into your applications, workflows, and systems.

## ✨ Features

- **🔐 Secure Authentication**: API key-based authentication with role-based access control
- **📊 Rate Limiting**: Configurable rate limits to prevent abuse
- **📁 File Support**: PDF and image formats (PNG, JPG, JPEG, TIFF, BMP, WebP)
- **🔄 Batch Processing**: Process multiple invoices in a single request
- **📈 Comprehensive Analysis**: Detailed invoice parsing, tax extraction, and price matching
- **🛡️ Error Handling**: Robust error handling with detailed error messages
- **📊 Monitoring**: Built-in status and rate limit monitoring endpoints
- **👥 User Management**: Admin tools for managing API users and keys

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │    │   API Server    │    │  OCR Engine     │
│                 │    │                 │    │                 │
│ • Web App      │───▶│ • Authentication│───▶│ • Text Extract  │
│ • Mobile App   │    │ • Rate Limiting │    │ • Invoice Parse │
│ • Integration  │    │ • File Handling │    │ • Price Match   │
│ • Workflow     │    │ • Response Gen  │    │ • Tax Extract   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_api.txt
```

### 2. Start the API Server

```bash
python api.py
```

The API will start on port 5001 (different from the web app on port 5000).

### 3. Test the API

```bash
python test_api.py
```

## 🔑 Authentication

All API endpoints require authentication using an API key in the `X-API-Key` header.

### Default API Keys

| Username | API Key | Role | Description |
|----------|---------|------|-------------|
| `admin` | `admin_api_key_12345` | Admin | Full access, user management |
| `team1` | `team1_api_key_67890` | User | Standard API access |

### Using API Keys

```bash
curl -H "X-API-Key: your_api_key_here" \
     http://localhost:5001/api/v1/status
```

## 📡 API Endpoints

### Core Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health` | GET | Health check | No |
| `/analyze` | POST | Analyze single invoice | Yes |
| `/batch-analyze` | POST | Analyze multiple invoices | Yes |
| `/status` | GET | Get API status | Yes |
| `/rate-limits` | GET | Get rate limit status | Yes |

### Admin Endpoints

| Endpoint | Method | Description | Admin Only |
|----------|--------|-------------|------------|
| `/users` | GET | List all users | Yes |
| `/users` | POST | Create new user | Yes |

## 📊 Rate Limits

| Time Period | Limit | Description |
|-------------|-------|-------------|
| Per Minute | 60 requests | Prevents rapid-fire requests |
| Per Hour | 1,000 requests | Hourly usage control |
| Per Day | 10,000 requests | Daily usage control |

## 🔧 Configuration

### Environment Variables

```bash
# API Security
export API_SECRET_KEY="your-super-secret-api-key"
export JWT_SECRET="your-jwt-secret-key"

# Optional: Enable debug mode
export API_DEBUG=true
```

### API Configuration

The API configuration can be modified in `api.py`:

```python
API_CONFIG = {
    'SECRET_KEY': 'your-secret-key',
    'MAX_FILE_SIZE': 16 * 1024 * 1024,  # 16MB
    'RATE_LIMIT': {
        'REQUESTS_PER_MINUTE': 60,
        'REQUESTS_PER_HOUR': 1000,
        'REQUESTS_PER_DAY': 10000
    }
}
```

## 📁 File Support

### Supported Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| PDF | `.pdf` | Portable Document Format |
| PNG | `.png` | Portable Network Graphics |
| JPEG | `.jpg`, `.jpeg` | Joint Photographic Experts Group |
| TIFF | `.tiff`, `.tif` | Tagged Image File Format |
| BMP | `.bmp` | Bitmap Image |
| WebP | `.webp` | Web Picture Format |

### File Requirements

- **Maximum Size**: 16MB
- **Quality**: Clear, readable text for best OCR results
- **Format**: Standard invoice layouts work best

## 🔍 Response Format

### Success Response

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
    "gst_rate": 18.0
  },
  "invoice_items": [...],
  "extracted_text": "Raw OCR text...",
  "analysis_timestamp": "2024-01-15T10:30:00",
  "api_user": "team1",
  "request_id": "req_1705312200_1234"
}
```

### Error Response

```json
{
  "error": "File type not allowed"
}
```

## 🧪 Testing

### Automated Testing

Run the comprehensive test suite:

```bash
python test_api.py
```

### Manual Testing

Test individual endpoints:

```bash
# Health check
curl http://localhost:5001/api/v1/health

# Analyze invoice
curl -X POST "http://localhost:5001/api/v1/analyze" \
  -H "X-API-Key: team1_api_key_67890" \
  -F "file=@invoice.pdf"

# Get status
curl -H "X-API-Key: team1_api_key_67890" \
     http://localhost:5001/api/v1/status
```

## 🔌 Integration Examples

### Python Integration

```python
import requests

class InvoiceAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {'X-API-Key': api_key}
    
    def analyze_invoice(self, file_path):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/analyze",
                headers=self.headers,
                files=files
            )
            return response.json()
    
    def batch_analyze(self, file_paths):
        files = [('files', open(path, 'rb')) for path in file_paths]
        response = requests.post(
            f"{self.base_url}/batch-analyze",
            headers=self.headers,
            files=files
        )
        return response.json()

# Usage
api = InvoiceAPI("http://localhost:5001/api/v1", "your_api_key")
result = api.analyze_invoice("invoice.pdf")
```

### JavaScript/Node.js Integration

```javascript
const FormData = require('form-data');
const fs = require('fs');

class InvoiceAPI {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }
    
    async analyzeInvoice(filePath) {
        const form = new FormData();
        form.append('file', fs.createReadStream(filePath));
        
        const response = await fetch(`${this.baseUrl}/analyze`, {
            method: 'POST',
            headers: {
                'X-API-Key': this.apiKey,
                ...form.getHeaders()
            },
            body: form
        });
        
        return response.json();
    }
}

// Usage
const api = new InvoiceAPI("http://localhost:5001/api/v1", "your_api_key");
const result = await api.analyzeInvoice("invoice.pdf");
```

## 🚨 Error Handling

### HTTP Status Codes

| Code | Description | Action |
|------|-------------|--------|
| 200 | Success | Process response data |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Verify API key |
| 403 | Forbidden | Check user permissions |
| 404 | Not Found | Verify endpoint URL |
| 429 | Rate Limited | Wait and retry later |
| 500 | Server Error | Contact support |

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `API key required` | Missing X-API-Key header | Add authentication header |
| `Invalid API key` | Wrong or expired key | Check API key validity |
| `Rate limit exceeded` | Too many requests | Wait and retry later |
| `File type not allowed` | Unsupported format | Use supported file types |
| `No file provided` | Missing file in request | Include file in form data |

## 🔒 Security Features

- **API Key Authentication**: Secure access control
- **Rate Limiting**: Prevents abuse and ensures fair usage
- **File Validation**: Secure file handling and validation
- **Input Sanitization**: Protection against malicious input
- **Error Message Sanitization**: No sensitive information in errors

## 📈 Performance

### Expected Response Times

| Operation | Time | Notes |
|-----------|------|-------|
| Health Check | <100ms | Simple status check |
| Status/Info | <200ms | User and rate limit info |
| Single Invoice | 2-15s | Depends on file size and complexity |
| Batch (10 files) | 20-150s | Parallel processing |

### Optimization Tips

1. **Use Batch Processing**: Process multiple files in one request
2. **Monitor Rate Limits**: Stay within limits to avoid delays
3. **File Quality**: Use clear, high-quality images for faster OCR
4. **Network**: Ensure stable network connection for large files

## 🚀 Production Deployment

### Environment Setup

```bash
# Production environment variables
export API_SECRET_KEY="production-secret-key-here"
export JWT_SECRET="production-jwt-secret-here"
export API_DEBUG=false
export FLASK_ENV=production
```

### Using a Production Server

```bash
# Install production WSGI server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 api:api_app
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements_api.txt .
RUN pip install -r requirements_api.txt

COPY . .
EXPOSE 5001

CMD ["python", "api.py"]
```

## 🔧 Troubleshooting

### Common Issues

#### 1. API Server Won't Start
- Check if port 5001 is available
- Verify Python dependencies are installed
- Check for syntax errors in api.py

#### 2. Authentication Errors
- Verify API key is correct
- Check X-API-Key header is present
- Ensure API key hasn't expired

#### 3. Rate Limiting
- Monitor your usage with `/rate-limits` endpoint
- Implement exponential backoff for retries
- Consider upgrading to higher limits if needed

#### 4. File Processing Errors
- Verify file format is supported
- Check file size is under 16MB
- Ensure file is not corrupted

### Debug Mode

Enable debug mode for detailed error information:

```bash
export API_DEBUG=true
python api.py
```

## 📚 Additional Resources

- **Full API Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Web Application**: [README_WEB.md](README_WEB.md)
- **OCR Logic**: [test_basic_ocr.py](test_basic_ocr.py)
- **Test Scripts**: [test_api.py](test_api.py)

## 🤝 Support

For technical support or questions:

1. **Check Documentation**: Review this README and API documentation
2. **Run Tests**: Use `test_api.py` to verify functionality
3. **Check Logs**: Enable debug mode for detailed error information
4. **Health Check**: Use `/health` endpoint to verify service status

## 📄 License

This API is part of the Invoice OCR Analysis system. Please refer to the main project license for usage terms.

---

**API Version**: 1.0.0  
**Last Updated**: January 2024  
**Maintainer**: Invoice OCR Analysis Team
