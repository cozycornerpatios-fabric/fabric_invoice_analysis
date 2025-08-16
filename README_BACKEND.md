# Invoice Processing Backend API

A powerful Flask-based REST API for processing invoices using OCR, tax extraction, and fabric matching capabilities.

## 🚀 Features

- **Multi-format Invoice Support**: Handles Sarom, Sujan Impex, Home Ideas/D'Decor, and generic formats
- **Advanced OCR**: PDF and image processing with Tesseract
- **Tax Extraction**: IGST, CGST, SGST, and Home Ideas totals
- **Fabric Matching**: CSV database integration with intelligent matching algorithms
- **File Management**: Upload, download, and delete invoice files
- **RESTful API**: Clean JSON endpoints for easy integration

## 🛠️ Installation

### Prerequisites

1. **Python 3.8+**
2. **Tesseract OCR** - Install system-wide or set environment variable
3. **Required system packages** (for image processing)

### Setup

1. **Clone/Download** the project files
2. **Install Python dependencies**:
   ```bash
   pip install -r requirements_backend.txt
   ```

3. **Set environment variables** (optional):
   ```bash
   export TESSERACT_CMD=/usr/bin/tesseract  # Path to tesseract
   export FLASK_DEBUG=True                   # Enable debug mode
   export PORT=5000                          # Custom port
   ```

4. **Run the backend**:
   ```bash
   python app.py
   ```

## 📡 API Endpoints

### Health & Status

#### `GET /health`
Health check endpoint
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "1.0.0"
}
```

#### `GET /stats`
Get system statistics
```json
{
  "total_files": 5,
  "total_size_bytes": 1048576,
  "total_size_mb": 1.0,
  "upload_folder": "uploads"
}
```

### File Management

#### `GET /files`
List all uploaded files
```json
{
  "files": [
    {
      "filename": "20240115_103000_invoice.pdf",
      "size": 1048576,
      "modified": "2024-01-15T10:30:00"
    }
  ],
  "total_files": 1
}
```

#### `POST /upload`
Upload and process an invoice file
- **Content-Type**: `multipart/form-data`
- **Body**: `file` field with invoice file

**Response**:
```json
{
  "success": true,
  "invoice_type": "Home Ideas",
  "items_found": 5,
  "matched_items": 4,
  "match_percentage": 80.0,
  "total_invoice_value": 6617.52,
  "total_csv_value": 6600.00,
  "invoice_items": [...],
  "tax_summary": {...}
}
```

#### `POST /process`
Process an existing file by path
- **Content-Type**: `application/json`
- **Body**: `{"file_path": "/path/to/file.pdf"}`

#### `GET /download/<filename>`
Download a specific file

#### `DELETE /delete/<filename>`
Delete a specific file

## 🔍 Invoice Processing

### Supported Formats

1. **Sarom Format**: `4.15 Mtr 720.00 Mtr 2,988.00`
2. **Sujan Impex**: HSN-based structured format
3. **Home Ideas/D'Decor**: Table-based format with totals
4. **Generic**: Fallback parser for unknown formats

### Tax Extraction

- **IGST**: Rate and amount detection
- **Output IGST**: Sujan Impex specific
- **CGST/SGST**: Sarom style invoices
- **Home Ideas Totals**: Complete breakdown including TCS

### Fabric Matching

- **CSV Integration**: Matches against `Update existing materials.csv`
- **Smart Algorithms**: Multiple matching strategies
- **Score-based Results**: Confidence scoring for matches

## 📊 Response Structure

### Invoice Processing Response

```json
{
  "success": true,
  "invoice_type": "Home Ideas",
  "text_extracted": 2500,
  "items_found": 5,
  "items_processed": 5,
  "matched_items": 4,
  "match_percentage": 80.0,
  "total_invoice_value": 6617.52,
  "total_csv_value": 6600.00,
  "value_difference": 17.52,
  "value_difference_pct": 0.3,
  "invoice_items": [
    {
      "material_name": "Fabric Name",
      "quantity": 4.15,
      "rate": 720.00,
      "amount": 2988.00,
      "csv_match": "Matched Fabric",
      "csv_price": 700.00,
      "csv_amount": 2905.00,
      "method": "Direct Substring",
      "score": 85.2,
      "status": "✅ MATCH"
    }
  ],
  "tax_summary": {
    "igst": {
      "amount": 499.60,
      "rate_pct": null,
      "lines_found": 3
    },
    "output_igst": null,
    "gst_rate": 5.0,
    "cgst": 330.76,
    "sgst": 330.76,
    "home_ideas_totals": {
      "sub_total": 9991.80,
      "courier_charges": 0.00,
      "add_charges": 0.00,
      "taxable_value": 9991.80,
      "tcs_amount": 0.00,
      "igst_amount": 499.60,
      "cgst_amount": 0.00,
      "sgst_amount": 0.00,
      "total_inc_taxes": 10491.40
    }
  },
  "processing_timestamp": "2024-01-15T10:30:00",
  "uploaded_file": {
    "original_name": "invoice.pdf",
    "saved_name": "20240115_103000_invoice.pdf",
    "file_path": "uploads/20240115_103000_invoice.pdf",
    "file_size": 1048576
  }
}
```

## 🧪 Testing

### Run Test Script

```bash
python test_api.py
```

### Manual Testing with curl

```bash
# Health check
curl http://localhost:5000/health

# Upload invoice
curl -X POST -F "file=@invoice.pdf" http://localhost:5000/upload

# List files
curl http://localhost:5000/files

# Process existing file
curl -X POST -H "Content-Type: application/json" \
     -d '{"file_path": "uploads/invoice.pdf"}' \
     http://localhost:5000/process
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 5000 | Server port |
| `FLASK_DEBUG` | False | Debug mode |
| `TESSERACT_CMD` | Auto-detect | Tesseract path |
| `UPLOAD_FOLDER` | uploads | File storage directory |

### File Size Limits

- **Maximum file size**: 16MB
- **Supported formats**: PDF, PNG, JPG, JPEG, TIFF, BMP, WEBP

## 🚨 Error Handling

All endpoints return appropriate HTTP status codes:

- **200**: Success
- **400**: Bad Request (invalid input)
- **404**: Not Found (file not found)
- **500**: Internal Server Error

Error responses include descriptive messages:

```json
{
  "error": "File type not allowed. Allowed types: pdf, png, jpg, jpeg, tif, tiff, bmp, webp"
}
```

## 🔒 Security Considerations

- **File validation**: Only allowed file types accepted
- **Secure filenames**: Timestamped, sanitized filenames
- **CORS enabled**: For frontend integration
- **File size limits**: Prevents abuse

## 📈 Performance

- **Asynchronous processing**: Non-blocking file operations
- **Efficient OCR**: Optimized image processing
- **Smart caching**: CSV fabric database loaded once
- **Memory management**: Proper file cleanup

## 🔗 Integration Examples

### Frontend Integration

```javascript
// Upload invoice
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('Processing results:', data);
  // Handle results
});
```

### Mobile App Integration

```python
import requests

# Upload invoice from mobile app
with open('invoice.jpg', 'rb') as f:
    files = {'file': f}
    response = requests.post('https://api.example.com/upload', files=files)
    
result = response.json()
print(f"Matched {result['matched_items']} out of {result['items_found']} items")
```

## 🆘 Troubleshooting

### Common Issues

1. **Tesseract not found**: Set `TESSERACT_CMD` environment variable
2. **File upload fails**: Check file size and format
3. **OCR quality poor**: Ensure high-resolution images/PDFs
4. **Memory errors**: Reduce file size or increase system memory

### Debug Mode

Enable debug mode for detailed error information:

```bash
export FLASK_DEBUG=True
python app.py
```

## 📝 License

This project is part of the Invoice Processing System.

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review error logs in debug mode
3. Verify file formats and sizes
4. Ensure all dependencies are installed
