# 🔍 Fabric Name Matcher

A robust, probability-based string matching system for matching fabric names extracted from invoices with database entries.

## 🚀 Features

### **Multiple Matching Algorithms**
- **Exact Match**: 100% confidence for identical strings
- **Substring Match**: High confidence for partial matches
- **Fuzzy Match**: Uses multiple algorithms (SequenceMatcher, Jaro-Winkler, Levenshtein, FuzzyWuzzy)
- **Semantic Match**: Considers fabric type, color, and pattern keywords

### **Intelligent String Normalization**
- Removes OCR artifacts, HSN codes, tax percentages
- Normalizes spacing and punctuation
- Handles variations in fabric naming conventions

### **Confidence Scoring**
- **HIGH**: 85%+ match score
- **MEDIUM**: 70-84% match score  
- **LOW**: 50-69% match score
- **NO_MATCH**: Below 50% threshold

### **Price Validation**
- Compares invoice rates with database prices
- Calculates price differences and percentages
- Color-coded tolerance levels (5%, 15%, >15%)

## 📁 Files

- **`fabric_matcher.py`**: Core matching engine with all algorithms
- **`integrate_parsing_matching.py`**: Integration script combining parsing + matching
- **`requirements_matcher.txt`**: Dependencies for the matching system
- **`test_basic_ocr.py`**: Invoice parsing (existing file)

## 🛠️ Installation

### 1. Install Dependencies
```bash
pip install -r requirements_matcher.txt
```

### 2. Set Environment Variables
```bash
# Supabase Configuration
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"
export DB_TABLE="materials_stage"  # Optional, defaults to "materials_stage"

# CSV Fallback (if Supabase not available)
export INVENTORY_CSV="/path/to/fabrics.csv"
```

## 🎯 Usage

### **Option 1: Standalone Fabric Matching**
```bash
python fabric_matcher.py
```
This runs with example data to demonstrate the matching algorithms.

### **Option 2: Full Integration (Parsing + Matching)**
```bash
# Process Home Ideas DDecor invoice
python integrate_parsing_matching.py uploads/Home_Ideas_DDecor.pdf

# Process Sujan Impex invoice  
python integrate_parsing_matching.py uploads/Sujan_Impex_Pvt._Ltd..pdf

# Process Sarom invoice
python integrate_parsing_matching.py uploads/Sarom.pdf
```

## 🔧 How It Works

### **1. String Normalization**
```python
# Input: "CASSIA - 101 Isstegz00 | 5%"
# Output: "cassia 101"
```

### **2. Multi-Algorithm Matching**
```python
# Try exact match first
if exact_match(parsed_name):
    return 100% confidence

# Try substring match
if substring_match(parsed_name):
    return 80-95% confidence

# Try fuzzy match (multiple algorithms)
if fuzzy_match(parsed_name):
    return 70-90% confidence

# Try semantic match
if semantic_match(parsed_name):
    return 50-80% confidence
```

### **3. Confidence Scoring**
- **Exact Match**: 100%
- **Substring**: 80-95% (based on length ratio)
- **Fuzzy**: 70-90% (average of multiple algorithms)
- **Semantic**: 50-80% (keyword matching)

## 📊 Example Output

```
🔍 NEW ROYAL (from Home_Ideas_DDecor.pdf)
   📏 Qty: 3.9, Rate: ₹549.0, Amount: ₹2141.1
   ✅ MATCH: NEW ROYAL FABRIC
   🎯 Algorithm: SUBSTRING_MATCH
   📊 Score: 88.5%
   🏷️ Confidence: HIGH
   💰 DB Price: ₹550.00
   📈 Price Diff: ₹1.00 (0.2%)
   🟢 Price within 5% tolerance
```

## 🎨 Customization

### **Adjust Matching Thresholds**
```python
# In fabric_matcher.py, modify these values:
SUBSTRING_MIN_SCORE = 60.0      # Default: 60%
FUZZY_MIN_SCORE = 70.0          # Default: 70%
SEMANTIC_MIN_SCORE = 50.0       # Default: 50%
```

### **Add Custom Keywords**
```python
# In semantic_match method:
fabric_types = {'cotton', 'silk', 'wool', 'linen', 'polyester', 'rayon', 'nylon', 'acrylic'}
colors = {'red', 'blue', 'green', 'yellow', 'black', 'white', 'brown', 'pink', 'purple', 'orange', 'gray', 'grey'}
patterns = {'striped', 'checked', 'floral', 'geometric', 'solid', 'print', 'embroidery'}
```

### **Database Schema Flexibility**
The system automatically handles additional fields from your database:
```python
additional_fields = {k: v for k, v in row.items() 
                    if k not in ["material_name", "default_purchase_price"]}
```

## 🔍 Troubleshooting

### **No Database Connection**
- Check Supabase credentials
- Verify CSV fallback path
- Ensure `materials_stage` table exists

### **Low Match Scores**
- Check string normalization
- Verify database fabric names are clean
- Adjust matching thresholds

### **Missing Dependencies**
```bash
pip install fuzzywuzzy python-Levenshtein jellyfish supabase
```

## 📈 Performance

- **Small Database** (<1000 fabrics): ~1-2 seconds per invoice
- **Medium Database** (1000-10000 fabrics): ~2-5 seconds per invoice
- **Large Database** (>10000 fabrics): ~5-10 seconds per invoice

## 🎯 Best Practices

1. **Clean Database Names**: Ensure `material_name` in database is normalized
2. **Consistent Naming**: Use consistent fabric naming conventions
3. **Regular Updates**: Keep database updated with new fabric types
4. **Monitor Scores**: Review low-confidence matches manually
5. **Price Validation**: Use price differences to validate matches

## 🔮 Future Enhancements

- **Machine Learning**: Train custom models on your fabric data
- **Image Recognition**: Match fabric patterns/colors from images
- **Batch Processing**: Process multiple invoices simultaneously
- **API Integration**: REST API for external systems
- **Dashboard**: Web interface for match review and management

---

**🎉 Ready to match your fabrics with high accuracy!**
