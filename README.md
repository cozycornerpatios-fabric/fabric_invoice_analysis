# 🧵 Fabric Invoice Analyzer

A powerful Flask application that analyzes PDF invoices and validates fabric details against a database, focusing on **Description**, **Quantity**, **Rate**, and **Amount** columns.

## ✨ Key Features

### 🔍 Invoice Analysis
- **Description of Goods**: Extract fabric names from invoice descriptions
- **Quantity Column**: Extract quantities in meters with unit validation
- **Rate Column**: Extract cost per meter with currency handling
- **Amount Column**: Extract calculated totals and validate calculations
- **Invoice Metadata**: Extract invoice number, vendor, and total amounts

### 📊 Database Comparison & Validation
- **Fabric Matching**: Advanced similarity algorithms for fabric name matching
- **Rate Comparison**: Compare invoice rates with database average costs
- **Stock Validation**: Check quantities against available stock levels
- **Calculation Verification**: Validate that Quantity × Rate = Amount
- **Visual Indicators**: Color-coded validation status (✅ Success, ⚠️ Warning, ❌ Error)

### 🎯 Validation Features
- **Quantity Validation**: ✅ Found / ❌ Missing
- **Rate Validation**: ✅ Reasonable / ⚠️ Significant difference from database
- **Amount Validation**: ✅ Matches calculation / ⚠️ Mismatch detected
- **Overall Invoice Health**: Summary statistics and validation status

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Clone the repository
git clone <your-repo>
cd vc

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Supabase credentials
```

### 2. Database Setup
```sql
-- Run the Supabase setup script
-- This creates the fabrics_master table with sample data
```

### 3. Run the Application
```bash
python app.py
```

### 4. Upload and Analyze
- Open http://localhost:5000 in your browser
- Upload a PDF invoice
- View analysis results in table format

## 📋 Sample Invoice Analysis

The system extracts and validates:

```
✅ Invoice Number: INV-2024-001
✅ Vendor: Agora Fabrics Pvt Ltd
✅ Total Amount: ₹104375.00

📊 Fabric Details:
1. Agora 3787 Rayure Biege
   Quantity: 25.5 meters ✅
   Rate: ₹1250.00/m ✅
   Amount: ₹31875.00 ✅
   Validation: ✅ Match (Quantity × Rate = Amount)

2. Agora 1208 Tandem Flame Marino
   Quantity: 30.0 meters ✅
   Rate: ₹1250.00/m ✅
   Amount: ₹37500.00 ✅
   Validation: ✅ Match (Quantity × Rate = Amount)
```

## 🔧 Technical Details

### Extraction Patterns
- **Description Patterns**: Fabric names with codes and specifications
- **Quantity Patterns**: Supports meters, yards, units with flexible detection
- **Rate Patterns**: Handles different currency symbols and rate formats
- **Amount Patterns**: Multiple extraction methods for line totals

### Database Comparison Logic
- **Similarity Algorithm**: Multi-factor similarity scoring (Jaccard, brand matching, number patterns)
- **Rate Validation**: Compares invoice rates with database costs (±50% tolerance)
- **Amount Validation**: Verifies mathematical accuracy of calculations
- **Stock Comparison**: Shows available stock vs. ordered quantities

### Validation Rules
- **Quantity**: Must be present and numeric
- **Rate**: Must be present and within reasonable range of database cost
- **Amount**: Must match calculated value (Quantity × Rate) within ₹1 tolerance

## 📁 File Structure

```
vc/
├── app.py                          # Main Flask application
├── templates/
│   └── index.html                 # Web interface with table format
├── fabrics_database.sql           # Database schema and sample data
├── supabase_setup.sql            # Supabase table creation
├── test_invoice_analysis.py      # Test script for functionality
├── requirements.txt               # Python dependencies
└── README.md                     # This file
```

## 🧪 Testing

Run the test script to verify functionality:

```bash
python test_invoice_analysis.py
```

This will test:
- Invoice text extraction
- Description, quantity, rate, and amount extraction
- Calculation validation
- Database comparison logic

## 🔍 Supported Invoice Formats

The system can handle various invoice layouts:
- **Table Format**: Standard tabular invoice layouts
- **Line Item Format**: Individual line items with descriptions
- **Mixed Formats**: Combination of different invoice styles
- **Multiple Languages**: English and common invoice terms

## 📈 Validation Results

### Success Indicators (✅)
- All required fields extracted successfully
- Calculations match within tolerance
- Rates are within reasonable range

### Warning Indicators (⚠️)
- Rate differs significantly from database
- Amount calculation has small discrepancy
- Some fields missing but others valid

### Error Indicators (❌)
- Critical fields missing (quantity, rate, amount)
- Large calculation discrepancies
- No database matches found

## 🚀 Future Enhancements

- **OCR Integration**: Better text extraction from scanned invoices
- **Machine Learning**: Improved fabric name matching
- **Batch Processing**: Multiple invoice analysis
- **Export Features**: CSV/Excel export of validation results
- **API Endpoints**: REST API for integration with other systems

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the test script output
2. Verify database connectivity
3. Review environment variables
4. Check invoice format compatibility

---

**Built with ❤️ for fabric industry professionals**
