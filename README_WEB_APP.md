# Invoice OCR Analysis Web Application

A modern, beautiful web frontend for the advanced OCR invoice analysis system that processes fabric invoices and matches them against a database.

## Features

### 🎯 **Core Functionality**
- **Multi-format Invoice Support**: Handles PDF, PNG, JPG, JPEG, TIFF, BMP, and WEBP files
- **Advanced OCR Processing**: Uses PyMuPDF, pdfplumber, and Tesseract for optimal text extraction
- **Universal Parser**: Automatically detects and parses different invoice formats (SAROM, Sujan Impex, Home Ideas, etc.)
- **Database Matching**: Matches invoice items against CSV fabric database with intelligent fuzzy matching
- **Price Analysis**: Comprehensive price comparison with detailed mismatch reporting

### 🎨 **Modern UI/UX**
- **Beautiful Design**: Gradient backgrounds, glassmorphism effects, and modern typography
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile devices
- **Interactive Elements**: Smooth animations, loading states, and intuitive user flow
- **Real-time Feedback**: Live progress indicators and detailed result displays

### 📊 **Comprehensive Analysis**
- **Summary Dashboard**: Overview cards showing total items, matches, and values
- **Detailed Tables**: Complete invoice item analysis with database matches
- **Tax Summary**: Extracted tax information (IGST, CGST, SGST, etc.)
- **Price Mismatch Analysis**: Categorized price differences with severity levels
- **Extracted Text Viewer**: Collapsible section showing raw OCR output

## Installation

### Prerequisites
- Python 3.8 or higher
- All dependencies from `test_basic_ocr.py` (see main README)
- Flask and web-specific dependencies

### Setup
1. **Install Python dependencies:**
   ```bash
   pip install -r requirements_web.txt
   ```

2. **Ensure OCR dependencies are installed:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install system dependencies:**
   - **Tesseract OCR**: Required for image processing
   - **CSV Database**: Ensure `Update existing materials.csv` is in the project root

### Environment Variables
Create a `.env` file or set environment variables:
```bash
# Optional: Tesseract path (if not in system PATH)
TESSERACT_CMD=/usr/bin/tesseract

# Database configuration
DB_TABLE=materials_stage
INVENTORY_CSV=Update existing materials.csv
RATE_TOLERANCE_PCT=0.10
```

## Usage

### Starting the Application
```bash
python app.py
```

The application will start on `http://localhost:5000`

### Using the Web Interface

1. **Upload Invoice**
   - Click "Choose File" to select your invoice
   - Supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP, WEBP
   - Click "Analyze Invoice" to start processing

2. **View Results**
   - **Summary Cards**: Quick overview of analysis results
   - **Overall Status**: Overall match quality assessment
   - **Tax Summary**: Extracted tax information
   - **Invoice Items Table**: Detailed item-by-item analysis
   - **Price Analysis**: Categorized price mismatches
   - **Extracted Text**: Raw OCR output for debugging

3. **Understanding Results**
   - **✅ EXACT MATCH**: Perfect price match with database
   - **⚠️ MINOR DIFFERENCE**: 0-2% price difference
   - **❌ SMALL DIFFERENCE**: 2-5% price difference
   - **❌ MODERATE DIFFERENCE**: 5-10% price difference
   - **❌ SIGNIFICANT DIFFERENCE**: 10-25% price difference
   - **❌ MAJOR DIFFERENCE**: >25% price difference

## Technical Architecture

### Backend (Flask)
- **`app.py`**: Main Flask application with OCR integration
- **File Processing**: Secure file upload with automatic cleanup
- **OCR Analysis**: Integrates with `test_basic_ocr.py` functions
- **API Endpoints**: RESTful endpoints for file upload and analysis

### Frontend (HTML/CSS/JavaScript)
- **`templates/index.html`**: Main application interface
- **`static/css/style.css`**: Modern, responsive styling
- **`static/js/script.js`**: Interactive functionality and data handling

### Key Features
- **Asynchronous Processing**: Non-blocking file analysis
- **Error Handling**: Comprehensive error reporting and recovery
- **Responsive Design**: Mobile-first approach with CSS Grid and Flexbox
- **Accessibility**: Semantic HTML and keyboard navigation support

## File Structure
```
├── app.py                          # Main Flask application
├── templates/
│   └── index.html                 # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css             # Application styling
│   └── js/
│       └── script.js             # Frontend functionality
├── requirements_web.txt           # Web app dependencies
├── test_basic_ocr.py             # Core OCR functionality
└── README_WEB_APP.md             # This file
```

## Supported Invoice Formats

### 1. **SAROM Format**
- Pattern: `4.15 Mtr 720.00 Mtr 2,988.00`
- Automatic detection and parsing
- Handles OCR variations and noise

### 2. **Sujan Impex Format**
- Structured table with HSN codes
- Quantity, rate, and amount extraction
- Supplier information matching

### 3. **Home Ideas/D'Decor Format**
- Complex table structures
- Order number and collection parsing
- Comprehensive tax extraction

### 4. **Generic Format**
- Fallback parser for unknown formats
- Intelligent pattern recognition
- Flexible matching algorithms

## Database Integration

### CSV Database
- **File**: `Update existing materials.csv`
- **Columns**: Material_name, Category, Default_purchase_price, Default supplier
- **Matching**: Intelligent fuzzy matching with confidence scores
- **Fallback**: Graceful handling when database is unavailable

### Matching Algorithms
- **Direct Substring**: Exact and partial name matches
- **Fuzzy Matching**: Levenshtein distance and similarity scoring
- **Token-based**: Word-level matching for complex names
- **Confidence Scoring**: Percentage-based match quality

## Performance & Security

### Performance Features
- **File Size Limits**: 16MB maximum file size
- **Automatic Cleanup**: Temporary files removed after processing
- **Efficient Processing**: Optimized OCR and parsing algorithms
- **Responsive UI**: Non-blocking operations with progress indicators

### Security Features
- **File Validation**: Strict file type checking
- **Secure Uploads**: Unique filename generation
- **Input Sanitization**: XSS protection and input validation
- **Error Handling**: Secure error messages without information leakage

## Troubleshooting

### Common Issues

1. **Template Not Found Error**
   - Ensure `templates/` directory exists
   - Check file permissions and paths

2. **OCR Processing Errors**
   - Verify Tesseract installation
   - Check file format compatibility
   - Ensure sufficient system resources

3. **Database Matching Issues**
   - Verify CSV file exists and is readable
   - Check CSV format and column names
   - Ensure proper encoding (UTF-8)

4. **File Upload Problems**
   - Check file size limits
   - Verify supported file formats
   - Ensure upload directory permissions

### Debug Mode
Enable debug mode for detailed error information:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## Customization

### Styling
- Modify `static/css/style.css` for visual changes
- Update color schemes and typography
- Customize responsive breakpoints

### Functionality
- Extend `static/js/script.js` for additional features
- Add new analysis types in the backend
- Integrate with additional databases

### Templates
- Modify `templates/index.html` for layout changes
- Add new sections or modify existing ones
- Customize result display formats

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Invoice OCR Analysis System. See the main project license for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the main project documentation
3. Open an issue in the project repository

---

**Built with ❤️ using Flask, modern CSS, and advanced OCR technology**
