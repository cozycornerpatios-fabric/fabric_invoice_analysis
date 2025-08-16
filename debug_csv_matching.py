#!/usr/bin/env python3
"""
Debug CSV Matching
Test the CSV matching function step by step.
"""

from test_basic_ocr import clean_fabric_name, remove_csv_prefix, find_csv_fabric_match, load_csv_fabrics

def debug_matching():
    print("🔍 Debugging CSV Matching")
    print("=" * 50)
    
    # Load CSV fabrics
    csv_fabrics = load_csv_fabrics()
    print(f"Loaded {len(csv_fabrics)} fabrics")
    
    # Test fabric
    test_fabric = "NEW ROYAL"
    print(f"\nTesting: '{test_fabric}'")
    
    # Clean test fabric
    test_cleaned = clean_fabric_name(test_fabric)
    print(f"Cleaned: '{test_cleaned}'")
    
    # Check first few CSV fabrics
    print(f"\nFirst 5 CSV fabrics:")
    for i, fabric in enumerate(csv_fabrics[:5]):
        csv_name = fabric['original_name']
        csv_cleaned = fabric['cleaned_name']
        csv_no_prefix = remove_csv_prefix(csv_name)
        csv_no_prefix_cleaned = clean_fabric_name(csv_no_prefix)
        
        print(f"  {i+1}. Original: '{csv_name}'")
        print(f"     Cleaned: '{csv_cleaned}'")
        print(f"     No Prefix: '{csv_no_prefix}'")
        print(f"     No Prefix Cleaned: '{csv_no_prefix_cleaned}'")
        
        # Check if test fabric is substring
        if test_cleaned in csv_no_prefix_cleaned:
            print(f"     ✅ SUBSTRING MATCH!")
        else:
            print(f"     ❌ No substring match")
    
    # Test matching with lower threshold
    print(f"\nTesting with threshold 0.3:")
    match = find_csv_fabric_match(test_fabric, csv_fabrics, threshold=0.3)
    print(f"Match found: {match is not None}")
    if match:
        print(f"Match details: {match}")

if __name__ == "__main__":
    debug_matching()
