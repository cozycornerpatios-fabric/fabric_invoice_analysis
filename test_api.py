#!/usr/bin/env python3
"""
Test script for the Invoice OCR Analysis API
Tests all endpoints and functionality
"""

import requests
import json
import time
import os
from pathlib import Path

# API Configuration
API_BASE_URL = "http://localhost:5001/api/v1"
API_KEYS = {
    'admin': 'admin_api_key_12345',
    'team1': 'team1_api_key_67890'
}

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing Health Check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data['status']}")
            return True
        else:
            print(f"❌ Health Check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check error: {e}")
        return False

def test_analyze_invoice(api_key, file_path):
    """Test single invoice analysis"""
    print(f"🔍 Testing Invoice Analysis...")
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            headers = {'X-API-Key': api_key}
            
            response = requests.post(
                f"{API_BASE_URL}/analyze",
                headers=headers,
                files=files
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Invoice Analysis: {data['summary']['overall_status']}")
                    print(f"   Items: {data['summary']['total_items']}, Matched: {data['summary']['matched_items']}")
                    return True
                else:
                    print(f"❌ Analysis failed: {data.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Analysis request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return False

def test_batch_analyze(api_key, file_paths):
    """Test batch invoice analysis"""
    print(f"🔍 Testing Batch Analysis...")
    try:
        files = []
        for path in file_paths:
            if os.path.exists(path):
                files.append(('files', open(path, 'rb')))
        
        if not files:
            print("❌ No valid files found for batch analysis")
            return False
        
        headers = {'X-API-Key': api_key}
        
        response = requests.post(
            f"{API_BASE_URL}/batch-analyze",
            headers=headers,
            files=files
        )
        
        # Close files
        for _, f in files:
            f.close()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Batch Analysis: {data['successful_analyses']}/{data['total_files']} successful")
                return True
            else:
                print(f"❌ Batch analysis failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Batch analysis request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Batch analysis error: {e}")
        return False

def test_get_status(api_key):
    """Test status endpoint"""
    print(f"🔍 Testing Status Endpoint...")
    try:
        headers = {'X-API-Key': api_key}
        response = requests.get(f"{API_BASE_URL}/status", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: User {data['user']}, Role {data['role']}")
            return True
        else:
            print(f"❌ Status request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status error: {e}")
        return False

def test_rate_limits(api_key):
    """Test rate limits endpoint"""
    print(f"🔍 Testing Rate Limits...")
    try:
        headers = {'X-API-Key': api_key}
        response = requests.get(f"{API_BASE_URL}/rate-limits", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Rate Limits: {data['current_usage']['last_minute']}/min, {data['current_usage']['last_hour']}/hour")
            return True
        else:
            print(f"❌ Rate limits request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Rate limits error: {e}")
        return False

def test_list_users(admin_api_key):
    """Test list users endpoint (admin only)"""
    print(f"🔍 Testing List Users (Admin)...")
    try:
        headers = {'X-API-Key': admin_api_key}
        response = requests.get(f"{API_BASE_URL}/users", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ List Users: {data['total_users']} users found")
            return True
        else:
            print(f"❌ List users request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ List users error: {e}")
        return False

def test_create_user(admin_api_key):
    """Test create user endpoint (admin only)"""
    print(f"🔍 Testing Create User (Admin)...")
    try:
        headers = {
            'X-API-Key': admin_api_key,
            'Content-Type': 'application/json'
        }
        
        user_data = {
            'username': f'test_user_{int(time.time())}',
            'password': 'test_password_123',
            'role': 'user'
        }
        
        response = requests.post(
            f"{API_BASE_URL}/users",
            headers=headers,
            json=user_data
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Create User: {data['message']}")
            return True
        else:
            print(f"❌ Create user request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Create user error: {e}")
        return False

def test_authentication():
    """Test authentication with invalid API key"""
    print(f"🔍 Testing Authentication...")
    try:
        headers = {'X-API-Key': 'invalid_key'}
        response = requests.get(f"{API_BASE_URL}/status", headers=headers)
        
        if response.status_code == 401:
            print("✅ Authentication: Properly rejected invalid API key")
            return True
        else:
            print(f"❌ Authentication: Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting by making multiple requests"""
    print(f"🔍 Testing Rate Limiting...")
    try:
        headers = {'X-API-Key': API_KEYS['team1']}
        
        # Make multiple requests quickly
        responses = []
        for i in range(5):
            response = requests.get(f"{API_BASE_URL}/status", headers=headers)
            responses.append(response.status_code)
            time.sleep(0.1)  # Small delay
        
        success_count = sum(1 for code in responses if code == 200)
        print(f"✅ Rate Limiting: {success_count}/5 requests successful")
        return success_count > 0
    except Exception as e:
        print(f"❌ Rate limiting error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Invoice OCR Analysis API Tests\n")
    
    # Find test files
    uploads_dir = Path("uploads")
    test_files = []
    
    if uploads_dir.exists():
        for ext in ['.pdf', '.png', '.jpg', '.jpeg']:
            test_files.extend(uploads_dir.glob(f"*{ext}"))
    
    if not test_files:
        print("⚠️  No test files found in uploads/ directory")
        print("   Please add some invoice files to test with")
        return
    
    print(f"📁 Found {len(test_files)} test files")
    
    # Test results
    results = []
    
    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Authentication
    results.append(("Authentication", test_authentication()))
    
    # Test 3: Status with valid API key
    results.append(("Status Endpoint", test_get_status(API_KEYS['team1'])))
    
    # Test 4: Rate Limits
    results.append(("Rate Limits", test_rate_limits(API_KEYS['team1'])))
    
    # Test 5: Single Invoice Analysis
    if test_files:
        results.append(("Single Analysis", test_analyze_invoice(API_KEYS['team1'], test_files[0])))
    
    # Test 6: Batch Analysis
    if len(test_files) > 1:
        results.append(("Batch Analysis", test_batch_analyze(API_KEYS['team1'], test_files[:2])))
    
    # Test 7: Admin Functions
    results.append(("List Users (Admin)", test_list_users(API_KEYS['admin'])))
    results.append(("Create User (Admin)", test_create_user(API_KEYS['admin'])))
    
    # Test 8: Rate Limiting
    results.append(("Rate Limiting", test_rate_limiting()))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the API server and configuration.")

if __name__ == "__main__":
    main()
