# OCR Testing Frontend

A modern, responsive web interface for testing Optical Character Recognition (OCR) functionality built with Flask and Tesseract.

## 🚀 Features

- **Modern UI/UX**: Beautiful gradient design with smooth animations
- **Drag & Drop**: Intuitive file upload with drag-and-drop support
- **Multiple Formats**: Supports PDF, PNG, JPG, JPEG, TIFF, BMP, WEBP
- **Real-time Processing**: Live progress tracking and results display
- **Responsive Design**: Works perfectly on desktop and mobile devices
- **Error Handling**: Comprehensive error messages and validation
- **File Management**: Automatic cleanup of uploaded files

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **OCR Engine**: Tesseract OCR
- **Image Processing**: Pillow (PIL), OpenCV
- **PDF Processing**: PyMuPDF, pdfplumber
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: Custom CSS with Font Awesome icons

## 📋 Prerequisites

### System Requirements
- Python 3.7+
- Tesseract OCR engine installed on your system

### Tesseract Installation

#### Windows
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH
3. Restart terminal/command prompt

#### macOS
```bash
brew install tesseract
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

#### Linux (CentOS/RHEL)
```bash
sudo yum install tesseract
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_ocr.txt
```

### 2. Test OCR Installation
```bash
python test_ocr_frontend.py
```

### 3. Run the Application
```bash
python app.py
```

### 4. Access the Interface
Open your browser and navigate to:
- **Main Interface**: http://localhost:5000/
- **OCR Testing**: http://localhost:5000/ocr-test

## 📁 Project Structure

```
vc/
├── app.py                          # Main Flask application with OCR routes
├── templates/
│   ├── index.html                 # Main invoice processing interface
│   └── ocr_test.html             # OCR testing interface
├── requirements_ocr.txt           # OCR-specific dependencies
├── test_ocr_frontend.py          # OCR functionality test script
└── README_OCR_FRONTEND.md        # This file
```

## 🔧 API Endpoints

### OCR Testing
- **GET** `/ocr-test` - OCR testing interface
- **POST** `/test-ocr` - Process uploaded file with OCR

### Request Format
```json
{
  "file": "multipart/form-data file upload"
}
```

### Response Format
```json
{
  "success": true,
  "filename": "document.pdf",
  "extracted_text": "Extracted text content...",
  "text_length": 1500,
  "confidence": "High"
}
```

## 🎨 Frontend Features

### Upload Interface
- Drag and drop file upload
- File type validation
- File information display
- Progress tracking

### Results Display
- Extracted text in formatted view
- Statistics (file name, text length, confidence)
- Responsive grid layout
- Scrollable text content

### User Experience
- Loading animations
- Error handling with user-friendly messages
- Responsive design for all screen sizes
- Smooth transitions and hover effects

## 🧪 Testing

### Run OCR Tests
```bash
python test_ocr_frontend.py
```

This script will test:
- Tesseract installation
- Pillow (PIL) functionality
- Basic OCR capabilities

### Manual Testing
1. Upload different file types (PDF, images)
2. Test with various text densities
3. Verify error handling with invalid files
4. Check responsive design on different screen sizes

## 🔍 Troubleshooting

### Common Issues

#### Tesseract Not Found
```
Error: TesseractNotFoundError
```
**Solution**: Install Tesseract OCR on your system (see Prerequisites)

#### Image Processing Errors
```
Error: PIL.UnidentifiedImageError
```
**Solution**: Ensure image files are not corrupted and in supported formats

#### PDF Processing Issues
```
Error: fitz.FileDataError
```
**Solution**: Check if PDF is password-protected or corrupted

#### Memory Issues
```
Error: MemoryError
```
**Solution**: Reduce image resolution or process smaller files

### Debug Mode
Enable debug mode in Flask for detailed error messages:
```python
app.run(debug=True, host="0.0.0.0", port=5000)
```

## 📱 Browser Compatibility

- **Chrome**: 90+ ✅
- **Firefox**: 88+ ✅
- **Safari**: 14+ ✅
- **Edge**: 90+ ✅
- **Mobile Browsers**: ✅

## 🎯 Use Cases

- **Document Digitization**: Convert scanned documents to searchable text
- **Invoice Processing**: Extract text from invoice images/PDFs
- **Form Processing**: Automate data entry from forms
- **Content Analysis**: Analyze text content from images
- **Accessibility**: Make image content accessible to screen readers

## 🔒 Security Features

- File type validation
- Secure filename handling
- Automatic file cleanup
- CORS configuration for development
- Input sanitization

## 📈 Performance Optimization

- Image preprocessing with OpenCV
- Efficient PDF processing with PyMuPDF
- Memory management for large files
- Asynchronous file processing
- Progress tracking for user feedback

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the Invoice Processing System and follows the same license terms.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Run the test script: `python test_ocr_frontend.py`
3. Review error logs in the Flask application
4. Ensure all dependencies are properly installed

## 🔮 Future Enhancements

- [ ] OCR confidence scoring
- [ ] Multiple language support
- [ ] Batch file processing
- [ ] Advanced image preprocessing
- [ ] Machine learning-based text correction
- [ ] Export functionality (TXT, DOCX, JSON)
- [ ] User authentication and file history
- [ ] API rate limiting and quotas
