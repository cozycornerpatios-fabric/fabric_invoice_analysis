#!/usr/bin/env python3
"""
Demo script to show the correct output format for invoice analysis
This shows exactly what data will be displayed in each column
"""

def show_demo_output():
    """Show the demo output format"""
    
    print("🧵 FABRIC INVOICE ANALYZER - DEMO OUTPUT")
    print("=" * 60)
    print("Focus: Description • Quantity • Rate • Amount")
    print("=" * 60)
    
    # Sample invoice data (what would be extracted from PDF)
    sample_invoice = [
        {
            'description': 'Agora 3787 Rayure Biege [1.60W] (59883)',
            'quantity': '25.5',
            'rate_per_meter': '1250.00',
            'amount': '31875.00',
            'calculated_amount': 31875.00
        },
        {
            'description': 'Agora 1208 Tandem Flame Marino [1.60W] (59753)',
            'quantity': '30.0',
            'rate_per_meter': '1250.00',
            'amount': '37500.00',
            'calculated_amount': 37500.00
        },
        {
            'description': 'Agora 1207 Tandem Flame Integral [1.60W] (00204)',
            'quantity': '28.0',
            'rate_per_meter': '1250.00',
            'amount': '35000.00',
            'calculated_amount': 35000.00
        }
    ]
    
    print("\n📋 INVOICE DETAILS - FABRIC ANALYSIS")
    print("-" * 60)
    print(f"{'Sr.':<4} {'Description of Goods':<40} {'Quantity':<12} {'Rate/m':<12} {'Amount':<12} {'Validation':<15}")
    print("-" * 60)
    
    for i, fabric in enumerate(sample_invoice, 1):
        # Calculate validation
        if fabric['calculated_amount'] and fabric['amount']:
            extracted = float(fabric['amount'])
            calculated = fabric['calculated_amount']
            difference = abs(extracted - calculated)
            if difference < 1:
                validation = "✅ Match"
            else:
                validation = f"⚠️ Diff: ₹{difference:.2f}"
        else:
            validation = "❌ Cannot Validate"
        
        print(f"{i:<4} {fabric['description']:<40} {fabric['quantity']:<12} ₹{fabric['rate_per_meter']:<11} ₹{fabric['amount']:<11} {validation:<15}")
    
    print("-" * 60)
    
    # Show calculation summary
    print("\n🧮 CALCULATION SUMMARY:")
    print("Formula: Amount = Quantity × Rate per Meter")
    print(f"Total Items: {len(sample_invoice)}")
    
    total_calculated = sum(float(f['calculated_amount']) for f in sample_invoice)
    print(f"Total Calculated: ₹{total_calculated:,.2f}")
    
    # Show what each column contains
    print("\n📊 COLUMN EXPLANATION:")
    print("• Description of Goods: Fabric names with codes and specifications")
    print("• Quantity: Amount in meters (e.g., 25.5 m)")
    print("• Rate per Meter: Cost per meter (e.g., ₹1250.00/m)")
    print("• Amount: Total cost for that item (e.g., ₹31875.00)")
    print("• Validation: Checks if Amount = Quantity × Rate")
    
    # Show database matching example
    print("\n🔍 DATABASE MATCHING EXAMPLE:")
    print("When you upload a real invoice, the system will:")
    print("1. Extract fabric names and match with database")
    print("2. Compare invoice rates with database costs")
    print("3. Show stock levels and SKU information")
    print("4. Validate calculations and flag discrepancies")

if __name__ == "__main__":
    show_demo_output()
