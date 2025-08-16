#!/usr/bin/env python3
"""
Test script for the real invoice format shown in the image
"""

from ocr import InvoiceOCR

def test_real_invoice_format():
    """Test OCR with the exact invoice format from the image"""
    
    # Real invoice text based on the image
    real_invoice_text = """
    SI No.    Description of Goods                    HSN/SAC    Quantity    Rate    per    Amount
    1.        Agora 3787 Rayure Biege [1.60W] (59883) 55122990   1.40 Mtr    1,250.00 Mtr    1,750.00
    2.        Agora 1208 Tandem Flame Marino [1.60W] (59753) 55122990   2.25 Mtr    1,250.00 Mtr    2,812.50
    3.        Agora 1207 Tandem Flame Integral [1.60W] (00204) 55122990   1.91 Mtr    1,250.00 Mtr    2,387.50
    
    Subtotal Amount: 6,950.00
    Output IGST-Delhi: 347.51
    """
    
    print("🧪 TESTING REAL INVOICE FORMAT")
    print("=" * 80)
    print("📄 Invoice Text:")
    print(real_invoice_text)
    print("=" * 80)
    
    # Create OCR instance
    ocr = InvoiceOCR()
    
    # Extract fabric details
    fabric_details = ocr.extract_fabric_details(real_invoice_text)
    
    print(f"🧵 Total Fabric Items Extracted: {len(fabric_details)}")
    print("\n📋 EXTRACTED FABRIC DETAILS:")
    print("-" * 100)
    print(f"{'SI':<4} {'Description':<45} {'HSN/SAC':<10} {'Qty':<8} {'Rate':<10} {'Per':<6} {'Amount':<12} {'Validation':<15}")
    print("-" * 100)
    
    for fabric in fabric_details:
        # Validation
        validation = "❌ Cannot Validate"
        if fabric['calculated_amount'] and fabric['amount']:
            try:
                extracted = float(fabric['amount'].replace(',', ''))
                calculated = fabric['calculated_amount']
                difference = abs(extracted - calculated)
                if difference < 1:
                    validation = "✅ Match"
                else:
                    validation = f"⚠️ Diff: ₹{difference:.2f}"
            except:
                validation = "❌ Error"
        
        # Display fabric details
        print(f"{fabric['si_no'] or 'N/A':<4} "
              f"{fabric['description'][:44]:<45} "
              f"{fabric['hsn_sac'] or 'N/A':<10} "
              f"{fabric['quantity'] or 'N/A':<8} "
              f"₹{fabric['rate_per_meter'] or 'N/A':<9} "
              f"{fabric['per_unit'] or 'N/A':<6} "
              f"₹{fabric['amount'] or 'N/A':<11} "
              f"{validation:<15}")
    
    print("-" * 100)
    
    # Show calculation examples
    print(f"\n🧮 CALCULATION VALIDATION:")
    print("-" * 50)
    for i, fabric in enumerate(fabric_details, 1):
        if fabric['quantity'] and fabric['rate_per_meter']:
            qty = float(fabric['quantity'])
            rate = float(fabric['rate_per_meter'].replace(',', ''))
            expected = qty * rate
            actual = float(fabric['amount'].replace(',', '')) if fabric['amount'] else 0
            
            print(f"{i}. {fabric['description'][:30]}...")
            print(f"   Quantity: {qty} m × Rate: ₹{rate}/m = ₹{expected:.2f}")
            print(f"   Invoice Amount: ₹{actual}")
            if abs(expected - actual) < 1:
                print(f"   ✅ Calculation matches!")
            else:
                print(f"   ⚠️ Difference: ₹{abs(expected - actual):.2f}")
            print()
    
    # Show summary
    print(f"📊 INVOICE SUMMARY:")
    print(f"• Total Items: {len(fabric_details)}")
    print(f"• Subtotal: ₹6,950.00")
    print(f"• IGST: ₹347.51")
    print(f"• Total: ₹7,297.51")

def test_individual_lines():
    """Test individual invoice lines"""
    
    print("\n🔍 TESTING INDIVIDUAL INVOICE LINES")
    print("=" * 60)
    
    # Individual lines from the invoice
    test_lines = [
        "1.        Agora 3787 Rayure Biege [1.60W] (59883) 55122990   1.40 Mtr    1,250.00 Mtr    1,750.00",
        "2.        Agora 1208 Tandem Flame Marino [1.60W] (59753) 55122990   2.25 Mtr    1,250.00 Mtr    2,812.50",
        "3.        Agora 1207 Tandem Flame Integral [1.60W] (00204) 55122990   1.91 Mtr    1,250.00 Mtr    2,387.50"
    ]
    
    ocr = InvoiceOCR()
    
    for i, line in enumerate(test_lines, 1):
        print(f"\n📝 Line {i}: {line}")
        
        fabric_details = ocr.extract_fabric_details(line)
        
        if fabric_details:
            fabric = fabric_details[0]
            print(f"   ✅ SI No.: {fabric['si_no']}")
            print(f"   ✅ Description: {fabric['description']}")
            print(f"   ✅ HSN/SAC: {fabric['hsn_sac']}")
            print(f"   ✅ Quantity: {fabric['quantity']} {fabric['per_unit']}")
            print(f"   ✅ Rate: ₹{fabric['rate_per_meter']}/{fabric['per_unit']}")
            print(f"   ✅ Amount: ₹{fabric['amount']}")
            
            # Validation
            if fabric['calculated_amount'] and fabric['amount']:
                try:
                    extracted = float(fabric['amount'].replace(',', ''))
                    calculated = fabric['calculated_amount']
                    difference = abs(extracted - calculated)
                    if difference < 1:
                        print(f"   ✅ Validation: PASS (Amount = Quantity × Rate)")
                    else:
                        print(f"   ⚠️ Validation: FAIL (Difference: ₹{difference:.2f})")
                except:
                    print(f"   ❌ Validation: ERROR")
        else:
            print(f"   ❌ No fabric details extracted")

if __name__ == "__main__":
    test_real_invoice_format()
    test_individual_lines()
    
    print("\n" + "=" * 80)
    print("💡 IMPROVEMENTS FOR REAL INVOICE FORMAT:")
    print("• Structured table parsing (SI No. | Description | HSN/SAC | Quantity | Rate | per | Amount)")
    print("• SI number extraction (1., 2., 3.)")
    print("• HSN/SAC code detection (8-digit codes like 55122990)")
    print("• Quantity with units (1.40 Mtr, 2.25 Mtr, 1.91 Mtr)")
    print("• Rate with comma formatting (1,250.00)")
    print("• Per unit detection (Mtr)")
    print("• Amount extraction and validation")
    print("• Multiple parsing methods for different line formats")
