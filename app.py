#!/usr/bin/env python3
"""
Invoice OCR Analysis Web Application
Frontend for the OCR invoice analysis functionality
"""

import os
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import uuid

# Import the OCR analysis functions from test_basic_ocr.py
from test_basic_ocr import (
    extract_text, UniversalInvoiceParser, load_csv_fabrics, 
    find_csv_fabric_match, extract_igst_lines, pick_invoice_igst,
    extract_output_igst_total, extract_cgst_sgst_roundoff,
    extract_homeideas_totals, load_db_items, compare
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_invoice(file_path):
    """Analyze invoice using the OCR logic from test_basic_ocr.py"""
    try:
        # Extract text from the uploaded file
        print(f"→ Extracting text from {file_path}...")
        text = extract_text(file_path)
        if not text:
            return {"error": "No text could be extracted from the file."}

        # Initialize parser and load databases
        parser = UniversalInvoiceParser()
        csv_fabrics = load_csv_fabrics()
        db_items = load_db_items()

        # Parse invoice items
        print("→ Parsing invoice items...")
        invoice_items = parser.parse_invoice(text)
        if not invoice_items:
            return {"error": "No valid fabric items found in the invoice."}

        # Extract tax information
        igst_lines = extract_igst_lines(text)
        best_igst = pick_invoice_igst(igst_lines)
        out_igst = extract_output_igst_total(text)
        taxes = extract_cgst_sgst_roundoff(text)
        totals = extract_homeideas_totals(text)

        # Analyze each invoice item
        analysis_results = []
        total_invoice_value = 0
        total_csv_value = 0
        matched_items = 0

        for item in invoice_items:
            # Find CSV match
            csv_match = find_csv_fabric_match(item.material_name, csv_fabrics)
            
            # Calculate amounts
            amount = item.amount if item.amount else (item.rate * item.quantity if item.rate and item.quantity else 0)
            total_invoice_value += amount

            analysis_item = {
                "material_name": item.material_name,
                "quantity": item.quantity,
                "rate": item.rate,
                "amount": amount,
                "csv_match": None,
                "price_analysis": None,
                "status": "❌ NOT MATCHED"
            }

            if csv_match:
                matched_items += 1
                csv_price = float(csv_match['fabric']['default_price']) if csv_match['fabric']['default_price'] else 0
                csv_amount = csv_price * item.quantity if item.quantity else 0
                total_csv_value += csv_amount

                analysis_item["csv_match"] = {
                    "database_name": csv_match['csv_name_no_prefix'],
                    "database_supplier": csv_match['fabric'].get('supplier', 'Unknown'),
                    "database_price": csv_price,
                    "match_method": csv_match['method'],
                    "confidence_score": csv_match['score']
                }

                # Price analysis
                if item.rate and csv_price:
                    price_diff = abs(item.rate - csv_price)
                    price_diff_pct = (price_diff / csv_price) * 100

                    if price_diff_pct == 0:
                        status = "✅ EXACT MATCH"
                        price_status = "✅ PRICE MATCHES"
                    elif price_diff_pct <= 2:
                        status = "⚠️ MINOR DIFFERENCE"
                        price_status = "⚠️ PRICE MINOR DIFFERENCE"
                    elif price_diff_pct <= 5:
                        status = "❌ SMALL DIFFERENCE"
                        price_status = "❌ PRICE DOESN'T MATCH (Small)"
                    elif price_diff_pct <= 10:
                        status = "❌ MODERATE DIFFERENCE"
                        price_status = "❌ PRICE DOESN'T MATCH (Moderate)"
                    elif price_diff_pct <= 25:
                        status = "❌ SIGNIFICANT DIFFERENCE"
                        price_status = "❌ PRICE DOESN'T MATCH (Significant)"
                    else:
                        status = "❌ MAJOR DIFFERENCE"
                        price_status = "❌ PRICE DOESN'T MATCH (Major)"

                    analysis_item["price_analysis"] = {
                        "invoice_rate": item.rate,
                        "database_price": csv_price,
                        "difference": price_diff,
                        "difference_percentage": price_diff_pct,
                        "status": status,
                        "price_status": price_status
                    }
                else:
                    status = "✅ MATCHED"
                    price_status = "✅ PRICE MATCHES"

                analysis_item["status"] = status
            else:
                analysis_item["status"] = "❌ NOT MATCHED"

            analysis_results.append(analysis_item)

        # Prepare summary statistics
        summary = {
            "total_items": len(invoice_items),
            "matched_items": matched_items,
            "unmatched_items": len(invoice_items) - matched_items,
            "match_percentage": (matched_items / len(invoice_items)) * 100 if invoice_items else 0,
            "total_invoice_value": total_invoice_value,
            "total_database_value": total_csv_value,
            "overall_status": "✅ EXCELLENT" if matched_items == len(invoice_items) else 
                             "⚠️ GOOD" if matched_items >= len(invoice_items) * 0.8 else
                             "❌ NEEDS ATTENTION" if matched_items >= len(invoice_items) * 0.5 else "❌ POOR"
        }

        # Prepare tax summary
        tax_summary = {}
        if best_igst and best_igst.amount is not None:
            tax_summary["igst_amount"] = best_igst.amount
        if out_igst and out_igst.amount is not None:
            tax_summary["output_igst"] = out_igst.amount
        if taxes.gst_rate is not None:
            tax_summary["gst_rate"] = taxes.gst_rate
        if taxes.cgst is not None:
            tax_summary["cgst"] = taxes.cgst
        if taxes.sgst is not None:
            tax_summary["sgst"] = taxes.sgst

        # Add Home Ideas totals
        if totals.sub_total is not None:
            tax_summary["sub_total"] = totals.sub_total
        if totals.courier_charges is not None:
            tax_summary["courier_charges"] = totals.courier_charges
        if totals.add_charges is not None:
            tax_summary["add_charges"] = totals.add_charges
        if totals.taxable_value is not None:
            tax_summary["taxable_value"] = totals.taxable_value
        if totals.tcs_amount is not None:
            tax_summary["tcs_amount"] = totals.tcs_amount
        if totals.igst_amount is not None:
            tax_summary["igst_amount"] = totals.igst_amount
        if totals.cgst_amount is not None:
            tax_summary["cgst_amount"] = totals.cgst_amount
        if totals.sgst_amount is not None:
            tax_summary["sgst_amount"] = totals.sgst_amount
        if totals.total_inc_taxes is not None:
            tax_summary["total_inc_taxes"] = totals.total_inc_taxes

        return {
            "success": True,
            "invoice_items": analysis_results,
            "summary": summary,
            "tax_summary": tax_summary,
            "extracted_text": text[:1000] + "..." if len(text) > 1000 else text  # First 1000 chars for debugging
        }

    except Exception as e:
        print(f"Error analyzing invoice: {str(e)}")
        traceback.print_exc()
        return {"error": f"Error analyzing invoice: {str(e)}"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'})
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        try:
            file.save(file_path)
            
            # Analyze the invoice
            result = analyze_invoice(file_path)
            
            # Clean up the uploaded file
            try:
                os.remove(file_path)
            except:
                pass  # Ignore cleanup errors
            
            return jsonify(result)
            
        except Exception as e:
            # Clean up on error
            try:
                os.remove(file_path)
            except:
                pass
            return jsonify({'error': f'Error processing file: {str(e)}'})
    
    return jsonify({'error': 'Invalid file type'})

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
