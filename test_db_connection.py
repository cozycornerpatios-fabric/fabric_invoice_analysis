#!/usr/bin/env python3
"""
Test Database Connection
Verifies connection to Supabase and shows available fabric data.
"""

import config  # This sets up the environment variables
from fabric_matcher import load_database_fabrics, DatabaseFabric

def test_connection():
    """Test the database connection and show available data"""
    print("🔗 Testing Supabase Database Connection")
    print("=" * 50)
    
    try:
        # Load fabrics from database
        fabrics = load_database_fabrics()
        
        if fabrics:
            print(f"✅ Successfully connected to Supabase!")
            print(f"📊 Found {len(fabrics)} fabric items in database")
            print("\n📋 Sample Fabric Data:")
            print("-" * 80)
            
            # Show first 10 fabrics as sample
            for i, fabric in enumerate(fabrics[:10]):
                print(f"{i+1:2d}. {fabric.material_name:<40} | ₹{fabric.default_purchase_price:>8.2f}")
            
            if len(fabrics) > 10:
                print(f"   ... and {len(fabrics) - 10} more items")
            
            print(f"\n📈 Database Statistics:")
            print(f"   Total Fabrics: {len(fabrics)}")
            
            # Price range analysis
            prices = [f.default_purchase_price for f in fabrics]
            if prices:
                print(f"   Price Range: ₹{min(prices):.2f} - ₹{max(prices):.2f}")
                print(f"   Average Price: ₹{sum(prices)/len(prices):.2f}")
            
            # Material name length analysis
            name_lengths = [len(f.material_name) for f in fabrics]
            if name_lengths:
                print(f"   Name Length Range: {min(name_lengths)} - {max(name_lengths)} characters")
                print(f"   Average Name Length: {sum(name_lengths)/len(name_lengths):.1f} characters")
            
            return True
            
        else:
            print("❌ No fabrics loaded from database")
            print("   This could mean:")
            print("   - Table is empty")
            print("   - Table doesn't exist")
            print("   - Column names don't match")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔍 Troubleshooting:")
        print("   1. Check if Supabase project is active")
        print("   2. Verify table 'materials_stage' exists")
        print("   3. Check column names: material_name, default_purchase_price")
        print("   4. Ensure table has data")
        return False

def show_table_structure():
    """Show the expected table structure"""
    print("\n📋 Expected Table Structure:")
    print("=" * 50)
    print("Table: materials_stage")
    print("Columns:")
    print("  - material_name (text)")
    print("  - default_purchase_price (numeric)")
    print("  - unit_of_measure (text) - optional")
    print("\nExample data:")
    print("  material_name           | default_purchase_price | unit_of_measure")
    print("  ----------------------- | ---------------------- | --------------")
    print("  NEW ROYAL FABRIC       | 550.00                 | MTR")
    print("  Agora Rayure Biege     | 1250.00                | MTR")
    print("  CASSIA 101             | 720.00                 | MTR")

if __name__ == "__main__":
    # Test the connection
    success = test_connection()
    
    if not success:
        show_table_structure()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Database connection successful! Ready for fabric matching.")
    else:
        print("⚠️ Database connection failed. Please check configuration.")
