#!/usr/bin/env python3
"""
Test Cost Matching: Invoice Fabric Costs vs Database Default Purchase Prices
Matches extracted fabric costs/quantities with database prices for validation.
"""

import config  # This sets up the environment variables
import sys
from pathlib import Path

# Import our custom modules
from fabric_matcher import FabricMatcher, ParsedFabric, DatabaseFabric, load_database_fabrics

# Import the parsing functionality from test_basic_ocr.py
sys.path.append('.')
try:
    from test_basic_ocr import UniversalInvoiceParser, extract_text
except ImportError:
    print("❌ Could not import parsing functionality. Make sure test_basic_ocr.py is in the same directory.")
    sys.exit(1)

def analyze_cost_matching(invoice_path: str):
    """
    Parse invoice and analyze cost matching with database
    """
    print(f"🔍 Analyzing Cost Matching for: {invoice_path}")
    print("=" * 80)
    
    # Step 1: Extract text from invoice
    print("📄 Extracting text from invoice...")
    text = extract_text(invoice_path)
    if not text:
        print("❌ No text extracted from invoice")
        return []
    
    # Step 2: Parse invoice using Universal Parser
    print("📋 Parsing invoice for fabric details...")
    parser = UniversalInvoiceParser()
    parsed_fabrics = parser.parse_invoice(text)
    
    if not parsed_fabrics:
        print("❌ No fabric items found in invoice")
        return []
    
    print(f"✅ Found {len(parsed_fabrics)} fabric items")
    
    # Step 3: Load database fabrics
    print("🔗 Loading database fabrics...")
    db_fabrics = load_database_fabrics()
    if not db_fabrics:
        print("❌ No database fabrics loaded")
        return []
    
    print(f"✅ Loaded {len(db_fabrics)} fabrics from database")
    
    # Step 4: Initialize fabric matcher
    print("🎯 Initializing fabric matcher...")
    matcher = FabricMatcher(db_fabrics)
    
    # Step 5: Match each parsed fabric and analyze costs
    print("\n🔍 Cost Matching Analysis:")
    print("-" * 80)
    
    results = []
    total_invoice_value = 0
    total_db_value = 0
    matched_count = 0
    price_discrepancies = []
    
    for i, fabric in enumerate(parsed_fabrics):
        print(f"\n{i+1:2d}. 🔍 {fabric.material_name}")
        print(f"    📏 Quantity: {fabric.quantity} | Invoice Rate: ₹{fabric.rate} | Amount: ₹{fabric.amount}")
        
        # Convert InvoiceLine to ParsedFabric
        parsed_fabric = ParsedFabric(
            material_name=fabric.material_name,
            quantity=fabric.quantity or 0,
            rate=fabric.rate or 0,
            amount=fabric.amount or 0,
            source_invoice=Path(invoice_path).name
        )
        
        # Match against database
        match_result = matcher.match_fabric(parsed_fabric)
        results.append(match_result)
        
        if match_result.database_fabric:
            matched_count += 1
            db_fabric = match_result.database_fabric
            db_price = db_fabric.default_purchase_price
            
            print(f"    ✅ MATCH: {db_fabric.material_name}")
            print(f"    🎯 Algorithm: {match_result.match_algorithm}")
            print(f"    📊 Score: {match_result.match_score:.1f}%")
            print(f"    🏷️ Confidence: {match_result.confidence_level}")
            print(f"    💰 DB Default Price: ₹{db_price}")
            
            # Calculate cost comparisons
            invoice_cost_per_unit = fabric.rate
            db_cost_per_unit = db_price
            cost_difference = abs(invoice_cost_per_unit - db_cost_per_unit)
            cost_difference_percent = (cost_difference / db_cost_per_unit) * 100
            
            # Calculate total values
            invoice_total = fabric.quantity * fabric.rate
            db_total = fabric.quantity * db_price
            total_invoice_value += invoice_total
            total_db_value += db_total
            
            print(f"    📊 Cost Analysis:")
            print(f"       Invoice Cost/Unit: ₹{invoice_cost_per_unit}")
            print(f"       DB Cost/Unit: ₹{db_cost_per_unit}")
            print(f"       Difference: ₹{cost_difference:.2f} ({cost_difference_percent:.1f}%)")
            
            # Price validation with color coding
            if cost_difference_percent <= 5:
                print(f"       🟢 Price within 5% tolerance - VALID")
            elif cost_difference_percent <= 15:
                print(f"       🟡 Price within 15% tolerance - REVIEW")
                price_discrepancies.append({
                    'fabric': fabric.material_name,
                    'invoice_price': invoice_cost_per_unit,
                    'db_price': db_cost_per_unit,
                    'difference_percent': cost_difference_percent,
                    'quantity': fabric.quantity,
                    'impact': cost_difference * fabric.quantity
                })
            else:
                print(f"       🔴 Price difference > 15% - INVESTIGATE")
                price_discrepancies.append({
                    'fabric': fabric.material_name,
                    'invoice_price': invoice_cost_per_unit,
                    'db_price': db_cost_per_unit,
                    'difference_percent': cost_difference_percent,
                    'quantity': fabric.quantity,
                    'impact': cost_difference * fabric.quantity
                })
            
            # Quantity validation
            calculated_amount = fabric.quantity * fabric.rate
            if abs(calculated_amount - fabric.amount) <= 1:  # Allow 1 rupee tolerance
                print(f"       ✅ Quantity × Rate = Amount calculation is correct")
            else:
                print(f"       ⚠️ Quantity × Rate ≠ Amount (Expected: ₹{calculated_amount}, Got: ₹{fabric.amount})")
                
        else:
            print(f"    ❌ NO MATCH FOUND")
            print(f"    📊 Best Score: {match_result.match_score:.1f}%")
            total_invoice_value += fabric.amount
    
    # Summary Report
    print("\n" + "=" * 80)
    print("📊 COST MATCHING SUMMARY REPORT")
    print("=" * 80)
    
    print(f"📋 Invoice: {Path(invoice_path).name}")
    print(f"🔍 Total Fabric Items: {len(parsed_fabrics)}")
    print(f"✅ Matched with Database: {matched_count}")
    print(f"❌ No Match Found: {len(parsed_fabrics) - matched_count}")
    print(f"📊 Match Rate: {(matched_count/len(parsed_fabrics)*100):.1f}%")
    
    if matched_count > 0:
        print(f"\n💰 Cost Analysis:")
        print(f"   Total Invoice Value: ₹{total_invoice_value:,.2f}")
        print(f"   Total DB Value: ₹{total_db_value:,.2f}")
        print(f"   Total Cost Difference: ₹{abs(total_invoice_value - total_db_value):,.2f}")
        
        if total_db_value > 0:
            overall_difference_percent = (abs(total_invoice_value - total_db_value) / total_db_value) * 100
            print(f"   Overall Difference: {overall_difference_percent:.1f}%")
    
    if price_discrepancies:
        print(f"\n⚠️ Price Discrepancies Found:")
        print("-" * 60)
        for disc in price_discrepancies:
            print(f"   {disc['fabric']:<30} | Invoice: ₹{disc['invoice_price']:>8.2f} | DB: ₹{disc['db_price']:>8.2f} | Diff: {disc['difference_percent']:>5.1f}% | Impact: ₹{disc['impact']:>8.2f}")
    
    return results

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_cost_matching.py /path/to/invoice.(pdf|png|jpg|...)")
        print("\nExample:")
        print("  python test_cost_matching.py uploads/Home_Ideas_DDecor.pdf")
        print("  python test_cost_matching.py uploads/Sujan_Impex_Pvt._Ltd..pdf")
        print("  python test_cost_matching.py uploads/Sarom.pdf")
        sys.exit(1)
    
    invoice_path = sys.argv[1]
    
    if not Path(invoice_path).exists():
        print(f"❌ File not found: {invoice_path}")
        sys.exit(1)
    
    print("🚀 Cost Matching Analysis: Invoice vs Database")
    print("=" * 80)
    
    # Analyze the invoice
    results = analyze_cost_matching(invoice_path)
    
    if results:
        print(f"\n🎯 Analysis Complete!")
        print(f"📊 Ready to validate fabric costs against your 8000+ fabric database!")
    else:
        print("❌ No results generated")

if __name__ == "__main__":
    main()
