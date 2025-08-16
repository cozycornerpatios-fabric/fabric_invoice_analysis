#!/usr/bin/env python3
"""
Test script to demonstrate quantity extraction from different invoice formats
"""

from ocr import InvoiceOCR

def test_different_quantity_formats():
    """Test OCR with various quantity formats found in invoices"""
    
    # Different invoice line formats with various quantity representations
    test_lines = [
        # Format 1: Standard format
        "1. Agora 3787 Rayure Biege [1.60W] (59883) 25.5 1250.00 31875.00",
        
        # Format 2: Quantity with units
        "2. Agora 1208 Tandem Flame Marino [1.60W] (59753) 30.0 m 1250.00 37500.00",
        
        # Format 3: Quantity with different units
        "3. Agora 1207 Tandem Flame Integral [1.60W] (00204) 28.0 mtr 1250.00 35000.00",
        
        # Format 4: Quantity with explicit labels
        "4. Agora 3790 Rayure Grey [1.60W] (59884) Qty: 15.5 1250.00 19375.00",
        
        # Format 5: Quantity in different position
        "5. Agora 3789 Rayure Navy [1.60W] (59885) 1250.00 22.0 27500.00",
        
        # Format 6: Quantity with @ symbol
        "6. Agora 1210 Tandem Flame White [1.60W] (00205) 18.5 @ 1250.00 23125.00",
        
        # Format 7: Quantity with x pattern (like 25.5 x 1.60)
        "7. Agora 3788 Rayure Brown [1.60W] (59886) 25.5 x 1.60 1250.00 31875.00",
        
        # Format 8: Very small quantities
        "8. Agora 1211 Tandem Flame Red [1.60W] (00206) 0.5 1250.00 625.00",
        
        # Format 9: Large quantities
        "9. Agora 1212 Tandem Flame Blue [1.60W] (00207) 500.0 1250.00 625000.00",
        
        # Format 10: Quantity with comma
        "10. Agora 1213 Tandem Flame Green [1.60W] (00208) 1,250.00 1250.00 1562500.00"
    ]
    
    print("🧪 TESTING QUANTITY EXTRACTION FROM DIFFERENT INVOICE FORMATS")
    print("=" * 80)
    
    # Create OCR instance
    ocr = InvoiceOCR()
    
    # Test each line
    for i, line in enumerate(test_lines, 1):
        print(f"\n📝 Line {i}: {line}")
        
        # Extract fabric details
        fabric_details = ocr.extract_fabric_details(line)
        
        if fabric_details:
            fabric = fabric_details[0]
            print(f"   ✅ Description: {fabric['description'][:40]}...")
            print(f"   📏 Quantity: {fabric['quantity'] or 'NOT FOUND'} m")
            print(f"   💰 Rate: ₹{fabric['rate_per_meter'] or 'NOT FOUND'}/m")
            print(f"   💵 Amount: ₹{fabric['amount'] or 'NOT FOUND'}")
            
            # Validation
            if fabric['calculated_amount'] and fabric['amount']:
                try:
                    extracted = float(fabric['amount'])
                    calculated = fabric['calculated_amount']
                    difference = abs(extracted - calculated)
                    if difference < 1:
                        print(f"   ✅ Validation: PASS (Amount = Quantity × Rate)")
                    else:
                        print(f"   ⚠️ Validation: FAIL (Difference: ₹{difference:.2f})")
                except:
                    print(f"   ❌ Validation: ERROR")
            else:
                print(f"   ❌ Validation: Cannot validate (missing data)")
        else:
            print(f"   ❌ No fabric details extracted")
    
    print("\n" + "=" * 80)
    print("📊 QUANTITY EXTRACTION METHODS USED:")
    print("1. Decimal numbers (25.5, 30.0, 28.0)")
    print("2. Numbers with units (25.5 m, 30 mtr, 28.0 meter)")
    print("3. Explicit labels (Qty: 15.5)")
    print("4. Position-based detection (after description, before rate)")
    print("5. Pattern matching (@ symbol, x pattern)")
    print("6. Range validation (0.1 to 1000 meters)")
    print("7. Context analysis (not rate or amount)")

def test_edge_cases():
    """Test edge cases and unusual formats"""
    
    print("\n🔍 TESTING EDGE CASES")
    print("=" * 50)
    
    edge_cases = [
        # Case 1: No quantity
        "Agora 9999 Test Fabric [1.60W] (99999) 1250.00 50000.00",
        
        # Case 2: Multiple numbers
        "Agora 8888 Multi Number [1.60W] (88888) 25.5 1250.00 31875.00 500.00",
        
        # Case 3: Very small decimal
        "Agora 7777 Small Qty [1.60W] (77777) 0.1 1250.00 125.00",
        
        # Case 4: Large whole number
        "Agora 6666 Large Qty [1.60W] (66666) 999 1250.00 1248750.00",
        
        # Case 5: Mixed units
        "Agora 5555 Mixed Units [1.60W] (55555) 25.5 mtr 1250.00 31875.00"
    ]
    
    ocr = InvoiceOCR()
    
    for i, line in enumerate(edge_cases, 1):
        print(f"\n📝 Edge Case {i}: {line}")
        
        fabric_details = ocr.extract_fabric_details(line)
        
        if fabric_details:
            fabric = fabric_details[0]
            print(f"   📏 Quantity: {fabric['quantity'] or 'NOT FOUND'}")
            print(f"   💰 Rate: ₹{fabric['rate_per_meter'] or 'NOT FOUND'}")
            print(f"   💵 Amount: ₹{fabric['amount'] or 'NOT FOUND'}")
        else:
            print(f"   ❌ No fabric details extracted")

if __name__ == "__main__":
    test_different_quantity_formats()
    test_edge_cases()
    
    print("\n" + "=" * 80)
    print("💡 KEY IMPROVEMENTS:")
    print("• Multiple extraction methods for different invoice formats")
    print("• Better handling of units (m, mtr, meter, yard, etc.)")
    print("• Position-based detection when patterns fail")
    print("• Range validation to distinguish quantity from rate/amount")
    print("• Support for various quantity formats (decimal, whole, with units)")
    print("• Fallback methods for complex invoice layouts")
