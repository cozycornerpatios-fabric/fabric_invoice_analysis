#!/usr/bin/env python3
"""
Test script for OCR Frontend
This script tests the OCR functionality without requiring the full Flask app
"""

import os
import sys
from PIL import Image
import pytesseract

def test_tesseract_installation():
    """Test if Tesseract is properly installed"""
    try:
        # Check if tesseract is available
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")
        return True
    except Exception as e:
        print(f"❌ Tesseract not available: {e}")
        print("Please install Tesseract OCR on your system:")
        print("Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("macOS: brew install tesseract")
        print("Linux: sudo apt-get install tesseract-ocr")
        return False

def test_pillow():
    """Test if Pillow (PIL) is working"""
    try:
        # Create a simple test image
        img = Image.new('RGB', (100, 30), color='white')
        print("✅ Pillow (PIL) is working")
        return True
    except Exception as e:
        print(f"❌ Pillow error: {e}")
        return False

def test_ocr_basic():
    """Test basic OCR functionality"""
    try:
        # Create a simple test image with text
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a white image
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font, fallback to basic if not available
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        # Draw some text
        draw.text((10, 15), "Hello World", fill='black', font=font)
        
        # Save test image
        test_image_path = "test_ocr_image.png"
        img.save(test_image_path)
        
        # Test OCR
        text = pytesseract.image_to_string(img)
        print(f"✅ Basic OCR test successful")
        print(f"   Extracted text: '{text.strip()}'")
        
        # Clean up
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Basic OCR test failed: {e}")
        return False

def test_dependencies():
    """Test all required dependencies"""
    print("🔍 Testing OCR Dependencies...")
    print("=" * 50)
    
    tests = [
        ("Tesseract Installation", test_tesseract_installation),
        ("Pillow (PIL)", test_pillow),
        ("Basic OCR", test_ocr_basic)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! OCR frontend should work correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

def main():
    """Main function"""
    print("🚀 OCR Frontend Test Suite")
    print("=" * 50)
    
    success = test_dependencies()
    
    if success:
        print("\n🎯 To test the full frontend:")
        print("1. Install requirements: pip install -r requirements_ocr.txt")
        print("2. Run Flask app: python app.py")
        print("3. Open browser: http://localhost:5000/ocr-test")
    else:
        print("\n🔧 Please fix the failing tests before using the OCR frontend.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
