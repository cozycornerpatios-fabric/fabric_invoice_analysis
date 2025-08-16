#!/usr/bin/env python3
"""
Integration Script: Combines Invoice Parsing with Fabric Matching
Takes parsed fabric data and matches it against the database.
"""

import os
import sys
from pathlib import Path
from typing import List

# Import our custom modules
from fabric_matcher import FabricMatcher, ParsedFabric, DatabaseFabric, load_database_fabrics

# Import the parsing functionality from test_basic_ocr.py
sys.path.append('.')
try:
    from test_basic_ocr import UniversalInvoiceParser, extract_text
except ImportError:
    print("❌ Could not import parsing functionality. Make sure test_basic_ocr.py is in the same directory.")
    sys.exit(1)

def parse_invoice_and_match(invoice_path: str) -> List[dict]:
    """
    Parse invoice and match fabrics against database
    Returns list of match results
    """
    print(f"🔍 Processing invoice: {invoice_path}")
    print("=" * 60)
    
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
    
    # Step 5: Match each parsed fabric
    print("\n🔍 Matching fabrics against database...")
    print("-" * 80)
    
    results = []
    for fabric in parsed_fabrics:
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
        
        # Display results
        print(f"\n🔍 {fabric.material_name}")
        print(f"   📏 Qty: {fabric.quantity}, Rate: ₹{fabric.rate}, Amount: ₹{fabric.amount}")
        
        if match_result.database_fabric:
            print(f"   ✅ MATCH: {match_result.database_fabric.material_name}")
            print(f"   🎯 Algorithm: {match_result.match_algorithm}")
            print(f"   📊 Score: {match_result.match_score:.1f}%")
            print(f"   🏷️ Confidence: {match_result.confidence_level}")
            print(f"   💰 DB Price: ₹{match_result.database_fabric.default_purchase_price}")
            
            if match_result.price_difference:
                print(f"   📈 Price Diff: ₹{match_result.price_difference:.2f} ({match_result.price_difference_percent:.1f}%)")
                
                if match_result.price_difference_percent <= 5:
                    print("   🟢 Price within 5% tolerance")
                elif match_result.price_difference_percent <= 15:
                    print("   🟡 Price within 15% tolerance")
                else:
                    print("   🔴 Price difference > 15%")
        else:
            print(f"   ❌ NO MATCH FOUND")
            print(f"   📊 Best Score: {match_result.match_score:.1f}%")
    
    return results

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python integrate_parsing_matching.py /path/to/invoice.(pdf|png|jpg|...)")
        print("\nExample:")
        print("  python integrate_parsing_matching.py uploads/Home_Ideas_DDecor.pdf")
        print("  python integrate_parsing_matching.py uploads/Sujan_Impex_Pvt._Ltd..pdf")
        print("  python integrate_parsing_matching.py uploads/Sarom.pdf")
        sys.exit(1)
    
    invoice_path = sys.argv[1]
    
    if not Path(invoice_path).exists():
        print(f"❌ File not found: {invoice_path}")
        sys.exit(1)
    
    print("🚀 Invoice Parsing + Fabric Matching Integration")
    print("=" * 60)
    
    # Process the invoice
    results = parse_invoice_and_match(invoice_path)
    
    if results:
        print(f"\n🎯 Processing Complete!")
        print(f"📊 Processed {len(results)} fabric items")
        
        # Summary statistics
        matched_count = sum(1 for r in results if r.database_fabric)
        high_confidence = sum(1 for r in results if r.confidence_level == "HIGH")
        medium_confidence = sum(1 for r in results if r.confidence_level == "MEDIUM")
        low_confidence = sum(1 for r in results if r.confidence_level == "LOW")
        no_match = sum(1 for r in results if r.confidence_level == "NO_MATCH")
        
        print(f"\n📈 Summary:")
        print(f"   ✅ Matched: {matched_count}")
        print(f"   🟢 High Confidence: {high_confidence}")
        print(f"   🟡 Medium Confidence: {medium_confidence}")
        print(f"   🟠 Low Confidence: {low_confidence}")
        print(f"   ❌ No Match: {no_match}")
    else:
        print("❌ No results generated")

if __name__ == "__main__":
    main()
