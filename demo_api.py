#!/usr/bin/env python3
"""
Demo Script for Smart Invoice OCR API
Shows how to use the API endpoints correctly
"""

import requests
import json
import os
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:5000"

def create_test_invoice():
    """Create a test invoice file"""
    test_content = """INVOICE

Company: Demo Corporation Ltd
Invoice #: INV-2025-001
Date: 15/08/2025

Items:
1. Premium Fabric - 10 yards - $50.00
2. Designer Material - 5 yards - $75.00
3. Luxury Textile - 8 yards - $60.00

Subtotal: $1,150.00
GST: $207.00
IGST: $0.00
Total: $1,357.00

Thank you for your business!
"""
    
    test_file = "demo_invoice.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    return test_file

def test_health():
    """Test health endpoint"""
    print("🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy!")
            print(f"   Status: {data.get('status', 'Unknown')}")
            print(f"   Version: {data.get('version', 'Unknown')}")
            print(f"   Timestamp: {data.get('timestamp', 'Unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return False

def test_upload_with_file(file_path):
    """Test upload endpoint with a file"""
    print(f"🔍 Testing Upload Endpoint with file: {file_path}")
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/upload", files=files)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'Not set')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ Upload successful!")
                print(f"   Filename: {data.get('filename', 'Unknown')}")
                print(f"   File Size: {data.get('file_size', 0)} bytes")
                print(f"   Text Length: {data.get('text_length', 0)} characters")
                
                # Show invoice data if available
                if 'invoice_data' in data:
                    inv_data = data['invoice_data']
                    print(f"   Company: {inv_data.get('company_name', 'Unknown')}")
                    print(f"   Invoice #: {inv_data.get('invoice_number', 'Unknown')}")
                    print(f"   Date: {inv_data.get('date', 'Unknown')}")
                    print(f"   Total: {inv_data.get('total_amount', 'Unknown')}")
                    
                    # Show tax details
                    tax_details = inv_data.get('tax_details', {})
                    if tax_details:
                        print("   Tax Details:")
                        for tax_type, amount in tax_details.items():
                            print(f"     {tax_type}: {amount}")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ Response is not valid JSON: {e}")
                print(f"   Response: {response.text[:200]}")
                return False
        else:
            try:
                error_data = response.json()
                print(f"❌ Upload failed: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"❌ Upload failed with status {response.status_code}")
                print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        print()

def test_ocr_with_file(file_path):
    """Test OCR endpoint with a file"""
    print(f"🔍 Testing OCR Endpoint with file: {file_path}")
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/test-ocr", files=files)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'Not set')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ OCR successful!")
                print(f"   Filename: {data.get('filename', 'Unknown')}")
                print(f"   Processing Time: {data.get('processing_time', 'Unknown')}")
                
                # Show extracted text preview
                extracted_text = data.get('extracted_text', '')
                if extracted_text:
                    print(f"   Extracted Text Preview:")
                    lines = extracted_text.split('\n')[:5]  # Show first 5 lines
                    for i, line in enumerate(lines, 1):
                        if line.strip():
                            print(f"     {i}: {line.strip()}")
                    if len(extracted_text.split('\n')) > 5:
                        print(f"     ... and {len(extracted_text.split('\n')) - 5} more lines")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ Response is not valid JSON: {e}")
                print(f"   Response: {response.text[:200]}")
                return False
        else:
            try:
                error_data = response.json()
                print(f"❌ OCR failed: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"❌ OCR failed with status {response.status_code}")
                print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        print()

def test_cleanup():
    """Test cleanup endpoint"""
    print("🔍 Testing Cleanup Endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/cleanup")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'Not set')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ Cleanup successful!")
                print(f"   Message: {data.get('message', 'Unknown')}")
                print(f"   Files Removed: {data.get('files_removed', 0)}")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ Response is not valid JSON: {e}")
                return False
        else:
            print(f"❌ Cleanup failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        print()

def main():
    """Main demo function"""
    print("🚀 Smart Invoice OCR API Demo")
    print("=" * 50)
    print()
    
    # Test health first
    if not test_health():
        print("❌ API is not healthy. Please check if the server is running.")
        return
    
    # Create test file
    test_file = create_test_invoice()
    print(f"📄 Created test file: {test_file}")
    print()
    
    try:
        # Test all endpoints
        results = []
        
        results.append(("Upload", test_upload_with_file(test_file)))
        results.append(("OCR", test_ocr_with_file(test_file)))
        results.append(("Cleanup", test_cleanup()))
        
        # Summary
        print("📊 Demo Results Summary")
        print("=" * 50)
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<15} {status}")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed! The API is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")
            
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n🧹 Cleaned up test file: {test_file}")

if __name__ == "__main__":
    main()
