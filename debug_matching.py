#!/usr/bin/env python3
"""
Debug Fabric Matching
Step-by-step debugging of the fabric matching process.
"""

import config  # This sets up the environment variables
from fabric_matcher import FabricMatcher, ParsedFabric, load_database_fabrics, normalize_string, tokenize_string

def debug_matching():
    """Debug the matching process step by step"""
    print("🔍 Debugging Fabric Matching Process")
    print("=" * 60)
    
    # Load database fabrics
    print("🔗 Loading database fabrics...")
    db_fabrics = load_database_fabrics()
    if not db_fabrics:
        print("❌ No database fabrics loaded")
        return
    
    print(f"✅ Loaded {len(db_fabrics)} fabrics from database")
    
    # Test fabric names from invoices
    test_fabrics = [
        "NEW ROYAL",
        "Agora 3787 Rayure Biege",
        "CASSIA - 101"
    ]
    
    for fabric_name in test_fabrics:
        print(f"\n🔍 Testing: '{fabric_name}'")
        print("-" * 50)
        
        # Show normalization
        normalized = normalize_string(fabric_name)
        print(f"   Normalized: '{normalized}'")
        
        # Show tokenization
        tokens = tokenize_string(fabric_name)
        print(f"   Tokens: {tokens}")
        
        # Test each matching algorithm separately
        matcher = FabricMatcher(db_fabrics)
        
        # Test exact match
        print(f"\n   🎯 Testing EXACT_MATCH...")
        exact_result = matcher.exact_match(fabric_name)
        if exact_result:
            db_fabric, score = exact_result
            print(f"      ✅ Found: {db_fabric.material_name} (Score: {score:.1f}%)")
        else:
            print(f"      ❌ No exact match")
        
        # Test prefix-based match
        print(f"   🎯 Testing PREFIX_BASED_MATCH...")
        prefix_result = matcher.prefix_based_match(fabric_name)
        if prefix_result:
            db_fabric, score = prefix_result
            print(f"      ✅ Found: {db_fabric.material_name} (Score: {score:.1f}%)")
        else:
            print(f"      ❌ No prefix-based match")
        
        # Test substring match
        print(f"   🎯 Testing SUBSTRING_MATCH...")
        substring_result = matcher.substring_match(fabric_name)
        if substring_result:
            db_fabric, score = substring_result
            print(f"      ✅ Found: {db_fabric.material_name} (Score: {score:.1f}%)")
        else:
            print(f"      ❌ No substring match")
        
        # Test fuzzy match
        print(f"   🎯 Testing FUZZY_MATCH...")
        fuzzy_result = matcher.fuzzy_match(fabric_name)
        if fuzzy_result:
            db_fabric, score = fuzzy_result
            print(f"      ✅ Found: {db_fabric.material_name} (Score: {score:.1f}%)")
        else:
            print(f"      ❌ No fuzzy match")
        
        # Test semantic match
        print(f"   🎯 Testing SEMANTIC_MATCH...")
        semantic_result = matcher.semantic_match(fabric_name)
        if semantic_result:
            db_fabric, score = semantic_result
            print(f"      ✅ Found: {db_fabric.material_name} (Score: {score:.1f}%)")
        else:
            print(f"      ❌ No semantic match")
        
        # Show best match from main function
        print(f"\n   🎯 Testing MAIN MATCH_FABRIC...")
        test_fabric = ParsedFabric(fabric_name, 1.0, 100.0, 100.0, "test")
        main_result = matcher.match_fabric(test_fabric)
        if main_result.database_fabric:
            print(f"      ✅ Final Result: {main_result.database_fabric.material_name}")
            print(f"      🎯 Algorithm: {main_result.match_algorithm}")
            print(f"      📊 Score: {main_result.match_score:.1f}%")
        else:
            print(f"      ❌ No final match found")
    
    # Show some database examples that might match
    print(f"\n🔍 Searching for potential matches in database:")
    print("-" * 60)
    
    # Look for fabrics with "ROYAL" in name
    royal_fabrics = [f for f in db_fabrics if "royal" in f.material_name.lower()]
    if royal_fabrics:
        print(f"   Fabrics with 'ROYAL':")
        for fabric in royal_fabrics[:5]:
            print(f"      - {fabric.material_name} | ₹{fabric.default_purchase_price}")
    
    # Look for fabrics with "NEW" in name
    new_fabrics = [f for f in db_fabrics if "new" in f.material_name.lower()]
    if new_fabrics:
        print(f"   Fabrics with 'NEW':")
        for fabric in new_fabrics[:5]:
            print(f"      - {fabric.material_name} | ₹{fabric.default_purchase_price}")
    
    # Look for fabrics with "HOME" or "DDECOR" in name
    home_fabrics = [f for f in db_fabrics if any(word in f.material_name.lower() for word in ["home", "ddecor"])]
    if home_fabrics:
        print(f"   Fabrics with 'HOME' or 'DDECOR':")
        for fabric in home_fabrics[:5]:
            print(f"      - {fabric.material_name} | ₹{fabric.default_purchase_price}")

if __name__ == "__main__":
    debug_matching()
