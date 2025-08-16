#!/usr/bin/env python3
"""
Test script to verify OCR endpoint functionality
"""

import requests
import os
from PIL import Image, ImageDraw, ImageFont

def create_test_image():
    """Create a simple test image with text"""
    # Create a white image
    img = Image.new('RGB', (300, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic if not available
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Draw some text
    draw.text((20, 35), "OCR Test Document", fill='black', font=font)
    draw.text((20, 65), "Sample Text for Testing", fill='black', font=font)
    
    # Save test image
    test_image_path = "test_ocr_endpoint.png"
    img.save(test_image_path)
    return test_image_path

def test_ocr_endpoint():
    """Test the OCR endpoint"""
    print("🧪 Testing OCR Endpoint...")
    
    # Create test image
    test_image_path = create_test_image()
    
    try:
        # Test the endpoint
        url = "http://localhost:5000/test-ocr"
        
        with open(test_image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OCR endpoint working successfully!")
            print(f"   Filename: {result.get('filename')}")
            print(f"   Text Length: {result.get('text_length')}")
            print(f"   Confidence: {result.get('confidence')}")
            print(f"   Extracted Text: {result.get('extracted_text', '')[:100]}...")
        else:
            print(f"❌ OCR endpoint failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app. Make sure it's running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error testing OCR endpoint: {e}")
    finally:
        # Clean up test image
        if os.path.exists(test_image_path):
            os.remove(test_image_path)

def test_ocr_interface():
    """Test if the OCR interface is accessible"""
    print("\n🧪 Testing OCR Interface...")
    
    try:
        response = requests.get("http://localhost:5000/ocr-test")
        if response.status_code == 200:
            print("✅ OCR interface accessible")
            print("   You can now open http://localhost:5000/ocr-test in your browser")
        else:
            print(f"❌ OCR interface not accessible. Status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app")
    except Exception as e:
        print(f"❌ Error testing OCR interface: {e}")

if __name__ == "__main__":
    print("🚀 OCR Endpoint Test Suite")
    print("=" * 50)
    
    test_ocr_endpoint()
    test_ocr_interface()
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. Open http://localhost:5000/ocr-test in your browser")
    print("2. Upload a document or image to test OCR")
    print("3. View the extracted text results")
