#!/usr/bin/env python3
"""
Invoice OCR Analysis API
RESTful API for integrating invoice analysis into team systems
"""

import os
import sys
import json
import traceback
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional, Union

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Import the OCR analysis functions
from test_basic_ocr import (
    extract_text, UniversalInvoiceParser, load_csv_fabrics,
    find_csv_fabric_match, extract_igst_lines, pick_invoice_igst,
    extract_output_igst_total, extract_cgst_sgst_roundoff,
    extract_homeideas_totals, load_db_items, compare
)

# API Configuration
API_CONFIG = {
    'SECRET_KEY': os.environ.get('API_SECRET_KEY', 'your-super-secret-api-key-change-in-production'),
    'JWT_SECRET': os.environ.get('JWT_SECRET', 'your-jwt-secret-key-change-in-production'),
    'JWT_EXPIRY_HOURS': 24,
    'MAX_FILE_SIZE': 16 * 1024 * 1024,  # 16MB
    'UPLOAD_FOLDER': 'uploads',
    'ALLOWED_EXTENSIONS': {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp', 'webp'},
    'RATE_LIMIT': {
        'REQUESTS_PER_MINUTE': 60,
        'REQUESTS_PER_HOUR': 1000,
        'REQUESTS_PER_DAY': 10000
    }
}

# Initialize Flask app for API
api_app = Flask(__name__)
api_app.config['SECRET_KEY'] = API_CONFIG['SECRET_KEY']
api_app.config['MAX_CONTENT_LENGTH'] = API_CONFIG['MAX_FILE_SIZE']

# Ensure upload directory exists
os.makedirs(API_CONFIG['UPLOAD_FOLDER'], exist_ok=True)

# In-memory storage for rate limiting (use Redis in production)
rate_limit_store = {}

# User management (use database in production)
users_db = {
    'admin': {
        'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
        'role': 'admin',
        'api_key': 'admin_api_key_12345'
    },
    'team1': {
        'password_hash': hashlib.sha256('team123'.encode()).hexdigest(),
        'role': 'user',
        'api_key': 'team1_api_key_67890'
    }
}

# API Key validation
def validate_api_key(api_key: str) -> Optional[Dict]:
    """Validate API key and return user info"""
    for username, user_data in users_db.items():
        if user_data['api_key'] == api_key:
            return {'username': username, 'role': user_data['role']}
    return None

# Rate limiting decorator
def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        user = validate_api_key(api_key)
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Rate limiting logic
        current_time = time.time()
        user_key = f"{user['username']}_{f.__name__}"
        
        if user_key not in rate_limit_store:
            rate_limit_store[user_key] = []
        
        # Clean old entries
        rate_limit_store[user_key] = [
            t for t in rate_limit_store[user_key] 
            if current_time - t < 3600  # Keep last hour
        ]
        
        # Check limits
        requests_last_minute = len([t for t in rate_limit_store[user_key] if current_time - t < 60])
        requests_last_hour = len([t for t in rate_limit_store[user_key] if current_time - t < 3600])
        requests_last_day = len([t for t in rate_limit_store[user_key] if current_time - t < 86400])
        
        if (requests_last_minute >= API_CONFIG['RATE_LIMIT']['REQUESTS_PER_MINUTE'] or
            requests_last_hour >= API_CONFIG['RATE_LIMIT']['REQUESTS_PER_HOUR'] or
            requests_last_day >= API_CONFIG['RATE_LIMIT']['REQUESTS_PER_DAY']):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Add current request
        rate_limit_store[user_key].append(current_time)
        
        return f(*args, **kwargs)
    return decorated_function

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        user = validate_api_key(api_key)
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401
        
        request.user = user
        return f(*args, **kwargs)
    return decorated_function

# Admin only decorator
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'user') or request.user['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Utility functions
def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in API_CONFIG['ALLOWED_EXTENSIONS']

def analyze_invoice_api(file_path: str) -> Dict:
    """Analyze invoice using the OCR logic"""
    try:
        # Extract text from file
        extracted_text = extract_text(file_path)
        
        # Parse invoice
        parser = UniversalInvoiceParser()
        invoice_data = parser.parse_invoice(file_path)
        
        if not invoice_data:
            return {'error': 'Could not parse invoice format'}
        
        # Load CSV fabrics for matching
        csv_fabrics = load_csv_fabrics()
        
        # Process each invoice line
        processed_items = []
        total_invoice_value = 0
        matched_items = 0
        
        for item in invoice_data.invoice_lines:
            # Find CSV match
            csv_match = find_csv_fabric_match(item.material_name, csv_fabrics)
            
            # Calculate price analysis if we have a match
            price_analysis = None
            if csv_match:
                matched_items += 1
                invoice_rate = item.rate or 0
                database_price = csv_match.database_price
                difference = abs(invoice_rate - database_price)
                difference_percentage = (difference / database_price * 100) if database_price > 0 else 0
                
                # Determine price status
                if difference_percentage == 0:
                    price_status = "EXACT MATCH"
                elif difference_percentage <= 2:
                    price_status = "MINOR DIFFERENCE"
                elif difference_percentage <= 5:
                    price_status = "SMALL DIFFERENCE"
                elif difference_percentage <= 10:
                    price_status = "MODERATE DIFFERENCE"
                elif difference_percentage <= 25:
                    price_status = "SIGNIFICANT DIFFERENCE"
                else:
                    price_status = "MAJOR DIFFERENCE"
                
                price_analysis = {
                    'invoice_rate': invoice_rate,
                    'database_price': database_price,
                    'difference': difference,
                    'difference_percentage': difference_percentage,
                    'price_status': price_status
                }
                
                # Determine overall status
                if difference_percentage == 0:
                    item.status = "EXACT MATCH"
                elif difference_percentage <= 2:
                    item.status = "MINOR DIFFERENCE"
                elif difference_percentage <= 5:
                    item.status = "SMALL DIFFERENCE"
                elif difference_percentage <= 10:
                    item.status = "MODERATE DIFFERENCE"
                elif difference_percentage <= 25:
                    item.status = "SIGNIFICANT DIFFERENCE"
                else:
                    item.status = "MAJOR DIFFERENCE"
            else:
                item.status = "NOT MATCHED"
            
            # Convert to dict for JSON serialization
            item_dict = {
                'material_name': item.material_name,
                'quantity': item.quantity,
                'rate': item.rate,
                'amount': item.amount,
                'status': item.status,
                'csv_match': csv_match.__dict__ if csv_match else None,
                'price_analysis': price_analysis
            }
            
            processed_items.append(item_dict)
            total_invoice_value += item.amount or 0
        
        # Calculate match percentage
        match_percentage = (matched_items / len(processed_items) * 100) if processed_items else 0
        
        # Determine overall status
        if match_percentage >= 90:
            overall_status = "EXCELLENT - 90%+ items matched"
        elif match_percentage >= 70:
            overall_status = "GOOD - 70-89% items matched"
        elif match_percentage >= 50:
            overall_status = "ATTENTION - 50-69% items matched"
        else:
            overall_status = "POOR - Less than 50% items matched"
        
        # Prepare tax summary
        tax_summary = {}
        
        # Extract IGST lines if available
        if hasattr(invoice_data, 'igst_lines') and invoice_data.igst_lines:
            igst_data = extract_output_igst_total(invoice_data.igst_lines)
            if igst_data:
                tax_summary.update({
                    'igst_amount': igst_data.igst_amount,
                    'output_igst': igst_data.output_igst,
                    'gst_rate': igst_data.gst_rate
                })
        
        # Extract CGST/SGST if available
        if hasattr(invoice_data, 'cgst_sgst_roundoff'):
            cgst_sgst = extract_cgst_sgst_roundoff(invoice_data.cgst_sgst_roundoff)
            if cgst_sgst:
                tax_summary.update({
                    'cgst': cgst_sgst.cgst,
                    'sgst': cgst_sgst.sgst,
                    'sub_total': cgst_sgst.sub_total,
                    'courier_charges': cgst_sgst.courier_charges,
                    'add_charges': cgst_sgst.add_charges,
                    'taxable_value': cgst_sgst.taxable_value,
                    'tcs_amount': cgst_sgst.tcs_amount,
                    'cgst_amount': cgst_sgst.cgst_amount,
                    'sgst_amount': cgst_sgst.sgst_amount,
                    'total_inc_taxes': cgst_sgst.total_inc_taxes
                })
        
        # Extract Home Ideas totals if available
        if hasattr(invoice_data, 'homeideas_totals'):
            homeideas = extract_homeideas_totals(invoice_data.homeideas_totals)
            if homeideas:
                tax_summary.update({
                    'sub_total': homeideas.sub_total,
                    'cgst': homeideas.cgst,
                    'sgst': homeideas.sgst,
                    'total': homeideas.total
                })
        
        # Prepare summary
        summary = {
            'total_items': len(processed_items),
            'matched_items': matched_items,
            'match_percentage': match_percentage,
            'total_invoice_value': total_invoice_value,
            'overall_status': overall_status
        }
        
        return {
            'success': True,
            'summary': summary,
            'tax_summary': tax_summary,
            'invoice_items': processed_items,
            'extracted_text': extracted_text,
            'analysis_timestamp': datetime.now().isoformat(),
            'file_processed': os.path.basename(file_path)
        }
        
    except Exception as e:
        return {
            'error': f'Analysis failed: {str(e)}',
            'traceback': traceback.format_exc() if API_CONFIG.get('DEBUG', False) else None
        }

# API Endpoints

@api_app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'service': 'Invoice OCR Analysis API'
    })

@api_app.route('/api/v1/analyze', methods=['POST'])
@require_auth
@rate_limit
def analyze_invoice_endpoint():
    """Analyze invoice endpoint"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(API_CONFIG['UPLOAD_FOLDER'], unique_filename)
        
        file.save(file_path)
        
        try:
            # Analyze the invoice
            result = analyze_invoice_api(file_path)
            
            # Add metadata
            result['api_user'] = request.user['username']
            result['request_id'] = f"req_{int(time.time())}_{hash(file_path) % 10000}"
            
            if result.get('success'):
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        finally:
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
                
    except Exception as e:
        return jsonify({
            'error': f'Processing failed: {str(e)}',
            'traceback': traceback.format_exc() if API_CONFIG.get('DEBUG', False) else None
        }), 500

@api_app.route('/api/v1/batch-analyze', methods=['POST'])
@require_auth
@rate_limit
def batch_analyze_endpoint():
    """Batch analyze multiple invoices"""
    try:
        # Check if files are present
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files selected'}), 400
        
        # Limit batch size
        if len(files) > 10:
            return jsonify({'error': 'Maximum 10 files allowed per batch'}), 400
        
        results = []
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
                
            if not allowed_file(file.filename):
                errors.append({
                    'filename': file.filename,
                    'error': 'File type not allowed'
                })
                continue
            
            try:
                # Save file temporarily
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(API_CONFIG['UPLOAD_FOLDER'], unique_filename)
                
                file.save(file_path)
                
                try:
                    # Analyze the invoice
                    result = analyze_invoice_api(file_path)
                    result['filename'] = file.filename
                    results.append(result)
                    
                finally:
                    # Clean up temporary file
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        
            except Exception as e:
                errors.append({
                    'filename': file.filename,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'total_files': len(files),
            'successful_analyses': len(results),
            'failed_analyses': len(errors),
            'results': results,
            'errors': errors,
            'batch_id': f"batch_{int(time.time())}",
            'api_user': request.user['username']
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Batch processing failed: {str(e)}',
            'traceback': traceback.format_exc() if API_CONFIG.get('DEBUG', False) else None
        }), 500

@api_app.route('/api/v1/status', methods=['GET'])
@require_auth
def get_status():
    """Get API status and user info"""
    return jsonify({
        'user': request.user['username'],
        'role': request.user['role'],
        'timestamp': datetime.now().isoformat(),
        'rate_limits': API_CONFIG['RATE_LIMIT'],
        'supported_formats': list(API_CONFIG['ALLOWED_EXTENSIONS']),
        'max_file_size_mb': API_CONFIG['MAX_FILE_SIZE'] / (1024 * 1024)
    })

@api_app.route('/api/v1/users', methods=['GET'])
@require_auth
@require_admin
def list_users():
    """List all users (admin only)"""
    user_list = []
    for username, user_data in users_db.items():
        user_list.append({
            'username': username,
            'role': user_data['role'],
            'api_key': user_data['api_key'][:8] + '...' if len(user_data['api_key']) > 8 else user_data['api_key']
        })
    
    return jsonify({
        'users': user_list,
        'total_users': len(user_list)
    })

@api_app.route('/api/v1/users', methods=['POST'])
@require_auth
@require_admin
def create_user():
    """Create new user (admin only)"""
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password required'}), 400
        
        username = data['username']
        password = data['password']
        role = data.get('role', 'user')
        
        if username in users_db:
            return jsonify({'error': 'Username already exists'}), 409
        
        # Generate API key
        api_key = f"{username}_api_key_{int(time.time())}"
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Add user
        users_db[username] = {
            'password_hash': password_hash,
            'role': role,
            'api_key': api_key
        }
        
        return jsonify({
            'success': True,
            'message': f'User {username} created successfully',
            'api_key': api_key
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'User creation failed: {str(e)}'}), 500

@api_app.route('/api/v1/rate-limits', methods=['GET'])
@require_auth
def get_rate_limits():
    """Get current rate limit status for user"""
    api_key = request.headers.get('X-API-Key')
    user = validate_api_key(api_key)
    
    current_time = time.time()
    user_key = f"{user['username']}_analyze_invoice_endpoint"
    
    if user_key in rate_limit_store:
        requests_last_minute = len([t for t in rate_limit_store[user_key] if current_time - t < 60])
        requests_last_hour = len([t for t in rate_limit_store[user_key] if current_time - t < 3600])
        requests_last_day = len([t for t in rate_limit_store[user_key] if current_time - t < 86400])
    else:
        requests_last_minute = 0
        requests_last_hour = 0
        requests_last_day = 0
    
    return jsonify({
        'user': user['username'],
        'current_usage': {
            'last_minute': requests_last_minute,
            'last_hour': requests_last_hour,
            'last_day': requests_last_day
        },
        'limits': API_CONFIG['RATE_LIMIT'],
        'remaining': {
            'last_minute': max(0, API_CONFIG['RATE_LIMIT']['REQUESTS_PER_MINUTE'] - requests_last_minute),
            'last_hour': max(0, API_CONFIG['RATE_LIMIT']['REQUESTS_PER_HOUR'] - requests_last_hour),
            'last_day': max(0, API_CONFIG['RATE_LIMIT']['REQUESTS_PER_DAY'] - requests_last_day)
        }
    })

# Error handlers
@api_app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@api_app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@api_app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Run API server
    api_app.run(
        debug=API_CONFIG.get('DEBUG', False),
        host='0.0.0.0',
        port=5001  # Different port from web app
    )
