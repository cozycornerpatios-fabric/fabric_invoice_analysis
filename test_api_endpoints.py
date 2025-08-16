#!/usr/bin/env python3
"""
API Testing Script for Smart Invoice OCR System
Tests all endpoints and helps debug issues
"""

import requests
import json
import os
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:5000"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return False

def test_main_page():
    """Test the main page endpoint"""
    print("🔍 Testing Main Page...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
        print(f"Response Length: {len(response.text)} characters")
        print(f"First 100 chars: {response.text[:100]}")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return False

def test_ocr_test_page():
    """Test the OCR test page endpoint"""
    print("🔍 Testing OCR Test Page...")
    try:
        response = requests.get(f"{BASE_URL}/ocr-test")
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
        print(f"Response Length: {len(response.text)} characters")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return False

def test_upload_endpoint_no_file():
    """Test upload endpoint without file (should return error)"""
    print("🔍 Testing Upload Endpoint (No File)...")
    try:
        response = requests.post(f"{BASE_URL}/upload")
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
        print(f"Response: {response.text}")
        print()
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return False

def test_upload_endpoint_with_file():
    """Test upload endpoint with a test file"""
    print("🔍 Testing Upload Endpoint (With File)...")
    
    # Create a simple test file
    test_file_path = "test_invoice.txt"
    try:
        with open(test_file_path, 'w') as f:
            f.write("Test Invoice\nCompany: Test Corp\nAmount: $100.00\nGST: $10.00")
        
        # Test file upload
        with open(test_file_path, 'rb') as f:
            files = {'file': (test_file_path, f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/upload", files=files)
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
        print(f"Response: {response.text}")
        
        # Try to parse as JSON
        try:
            json_response = response.json()
            print("✅ Response is valid JSON")
            print(f"JSON Keys: {list(json_response.keys())}")
        except json.JSONDecodeError as e:
            print(f"❌ Response is NOT valid JSON: {e}")
            print(f"Response starts with: {response.text[:200]}")
        
        print()
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_test_ocr_endpoint():
    """Test the test-ocr endpoint"""
    print("🔍 Testing Test-OCR Endpoint...")
    
    # Create a simple test file
    test_file_path = "test_image.txt"
    try:
        with open(test_file_path, 'w') as f:
            f.write("Test Image Content\nOCR Test Data")
        
        # Test file upload
        with open(test_file_path, 'rb') as f:
            files = {'file': (test_file_path, f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/test-ocr", files=files)
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
        print(f"Response: {response.text}")
        
        # Try to parse as JSON
        try:
            json_response = response.json()
            print("✅ Response is valid JSON")
            print(f"JSON Keys: {list(json_response.keys())}")
        except json.JSONDecodeError as e:
            print(f"❌ Response is NOT valid JSON: {e}")
            print(f"Response starts with: {response.text[:200]}")
        
        print()
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_cleanup_endpoint():
    """Test the cleanup endpoint"""
    print("🔍 Testing Cleanup Endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/cleanup")
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
        print(f"Response: {response.text}")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return False

def test_all_endpoints():
    """Test all endpoints"""
    print("🚀 Testing All API Endpoints")
    print("=" * 50)
    
    results = []
    
    # Test all endpoints
    results.append(("Health", test_health_endpoint()))
    results.append(("Main Page", test_main_page()))
    results.append(("OCR Test Page", test_ocr_test_page()))
    results.append(("Upload (No File)", test_upload_endpoint_no_file()))
    results.append(("Upload (With File)", test_upload_endpoint_with_file()))
    results.append(("Test OCR", test_test_ocr_endpoint()))
    results.append(("Cleanup", test_cleanup_endpoint()))
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 50)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")

def test_specific_endpoint(endpoint):
    """Test a specific endpoint"""
    print(f"🔍 Testing Specific Endpoint: {endpoint}")
    print("=" * 50)
    
    try:
        if endpoint == "health":
            response = requests.get(f"{BASE_URL}/health")
        elif endpoint == "main":
            response = requests.get(f"{BASE_URL}/")
        elif endpoint == "ocr-test":
            response = requests.get(f"{BASE_URL}/ocr-test")
        elif endpoint == "upload":
            response = requests.post(f"{BASE_URL}/upload")
        elif endpoint == "test-ocr":
            response = requests.post(f"{BASE_URL}/test-ocr")
        elif endpoint == "cleanup":
            response = requests.post(f"{BASE_URL}/cleanup")
        else:
            print(f"❌ Unknown endpoint: {endpoint}")
            return
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
        print(f"Response Length: {len(response.text)} characters")
        print(f"Response Preview: {response.text[:500]}")
        
        # Check if it's JSON
        if 'application/json' in response.headers.get('content-type', ''):
            try:
                json_response = response.json()
                print("✅ Valid JSON response")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
        else:
            print("ℹ️ Not a JSON response")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test specific endpoint
        endpoint = sys.argv[1]
        test_specific_endpoint(endpoint)
    else:
        # Test all endpoints
        test_all_endpoints()
    
    print("\n💡 Usage:")
    print("  python test_api_endpoints.py           # Test all endpoints")
    print("  python test_api_endpoints.py health   # Test health endpoint")
    print("  python test_api_endpoints.py upload   # Test upload endpoint")
    print("  python test_api_endpoints.py main     # Test main page")
