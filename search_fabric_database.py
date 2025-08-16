#!/usr/bin/env python3
"""
Search Fabric Database
Search for specific fabric names and show similar matches in the database.
"""

import config  # This sets up the environment variables
from fabric_matcher import load_database_fabrics, normalize_string
from difflib import get_close_matches

def search_fabric_database():
    """Search the fabric database for specific patterns"""
    print("🔍 Searching Fabric Database")
    print("=" * 50)
    
    # Load database fabrics
    print("🔗 Loading database fabrics...")
    db_fabrics = load_database_fabrics()
    if not db_fabrics:
        print("❌ No database fabrics loaded")
        return
    
    print(f"✅ Loaded {len(db_fabrics)} fabrics from database")
    
    # Search for specific patterns
    search_patterns = [
        "NEW ROYAL",
        "ROYAL",
        "AGORA",
        "CASSIA",
        "ALESIA",
        "KEIBA"
    ]
    
    print(f"\n🔍 Searching for fabric patterns:")
    print("-" * 50)
    
    for pattern in search_patterns:
        print(f"\n📋 Searching for: '{pattern}'")
        
        # Exact matches
        exact_matches = [f for f in db_fabrics if pattern.lower() in f.material_name.lower()]
        
        # Similar matches using difflib
        normalized_pattern = normalize_string(pattern)
        all_names = [normalize_string(f.material_name) for f in db_fabrics]
        similar_matches = get_close_matches(normalized_pattern, all_names, n=5, cutoff=0.6)
        
        if exact_matches:
            print(f"   ✅ Found {len(exact_matches)} exact matches:")
            for match in exact_matches[:3]:  # Show first 3
                print(f"      - {match.material_name} | ₹{match.default_purchase_price}")
            if len(exact_matches) > 3:
                print(f"      ... and {len(exact_matches) - 3} more")
        else:
            print(f"   ❌ No exact matches found")
        
        if similar_matches:
            print(f"   🔍 Found {len(similar_matches)} similar matches:")
            for similar in similar_matches:
                # Find the original fabric object
                original_fabrics = [f for f in db_fabrics if normalize_string(f.material_name) == similar]
                if original_fabrics:
                    fabric = original_fabrics[0]
                    print(f"      - {fabric.material_name} | ₹{fabric.default_purchase_price}")
        
        if not exact_matches and not similar_matches:
            print(f"   ⚠️ No matches found")
    
    # Show some sample fabric names from database
    print(f"\n📋 Sample Fabric Names from Database:")
    print("-" * 50)
    
    # Show fabrics with "ROYAL" in name
    royal_fabrics = [f for f in db_fabrics if "royal" in f.material_name.lower()]
    if royal_fabrics:
        print(f"   Fabrics with 'ROYAL':")
        for fabric in royal_fabrics[:5]:
            print(f"      - {fabric.material_name} | ₹{fabric.default_purchase_price}")
    
    # Show fabrics with "AGORA" in name
    agora_fabrics = [f for f in db_fabrics if "agora" in f.material_name.lower()]
    if agora_fabrics:
        print(f"   Fabrics with 'AGORA':")
        for fabric in agora_fabrics[:5]:
            print(f"      - {fabric.material_name} | ₹{fabric.default_purchase_price}")
    
    # Show some random sample fabrics
    print(f"   Random Sample Fabrics:")
    import random
    sample_fabrics = random.sample(db_fabrics, min(10, len(db_fabrics)))
    for fabric in sample_fabrics:
        print(f"      - {fabric.material_name} | ₹{fabric.default_purchase_price}")

def test_matching_algorithms():
    """Test different matching algorithms with sample data"""
    print(f"\n🧪 Testing Matching Algorithms:")
    print("-" * 50)
    
    from fabric_matcher import FabricMatcher
    
    # Load database fabrics
    db_fabrics = load_database_fabrics()
    matcher = FabricMatcher(db_fabrics)
    
    # Test fabrics from invoices
    test_fabrics = [
        "NEW ROYAL",
        "Agora 3787 Rayure Biege",
        "CASSIA - 101",
        "ALESIA-711",
        "KEIBA -912"
    ]
    
    for fabric_name in test_fabrics:
        print(f"\n🔍 Testing: '{fabric_name}'")
        
        # Create a dummy ParsedFabric for testing
        from fabric_matcher import ParsedFabric
        test_fabric = ParsedFabric(fabric_name, 1.0, 100.0, 100.0, "test")
        
        # Test matching
        result = matcher.match_fabric(test_fabric)
        
        if result.database_fabric:
            print(f"   ✅ MATCH: {result.database_fabric.material_name}")
            print(f"   🎯 Algorithm: {result.match_algorithm}")
            print(f"   📊 Score: {result.match_score:.1f}%")
            print(f"   🏷️ Confidence: {result.confidence_level}")
        else:
            print(f"   ❌ NO MATCH FOUND")
            print(f"   📊 Best Score: {result.match_score:.1f}%")

if __name__ == "__main__":
    # Search the database
    search_fabric_database()
    
    # Test matching algorithms
    test_matching_algorithms()
    
    print(f"\n" + "=" * 50)
    print("🔍 Database search complete!")
