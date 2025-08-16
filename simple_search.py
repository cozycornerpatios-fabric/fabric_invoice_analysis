#!/usr/bin/env python3
"""
Simple Fabric Search
Search for specific fabric patterns in the database.
"""

import config
from fabric_matcher import load_database_fabrics

def search_fabrics():
    """Search for specific fabric patterns"""
    print("Searching Fabric Database")
    print("=" * 50)
    
    # Load database fabrics
    print("Loading database fabrics...")
    db_fabrics = load_database_fabrics()
    if not db_fabrics:
        print("No database fabrics loaded")
        return
    
    print(f"Loaded {len(db_fabrics)} fabrics from database")
    
    # Search for specific patterns
    search_patterns = [
        "ROYAL",
        "NEW",
        "CASSIA",
        "HOME",
        "DDECOR",
        "SUJAN"
    ]
    
    print(f"\nSearching for fabric patterns:")
    print("-" * 50)
    
    for pattern in search_patterns:
        print(f"\nSearching for: '{pattern}'")
        
        # Exact matches
        exact_matches = [f for f in db_fabrics if pattern.lower() in f.material_name.lower()]
        
        if exact_matches:
            print(f"   Found {len(exact_matches)} exact matches:")
            for match in exact_matches[:5]:  # Show first 5
                print(f"      - {match.material_name} | Rs.{match.default_purchase_price}")
            if len(exact_matches) > 5:
                print(f"      ... and {len(exact_matches) - 5} more")
        else:
            print(f"   No exact matches found")
    
    # Show some sample fabric names from database
    print(f"\nSample Fabric Names from Database:")
    print("-" * 50)
    
    # Show fabrics with "ROYAL" in name
    royal_fabrics = [f for f in db_fabrics if "royal" in f.material_name.lower()]
    if royal_fabrics:
        print(f"   Fabrics with 'ROYAL':")
        for fabric in royal_fabrics[:5]:
            print(f"      - {fabric.material_name} | Rs.{fabric.default_purchase_price}")
    
    # Show fabrics with "HOME" or "DDECOR" in name
    home_fabrics = [f for f in db_fabrics if any(word in f.material_name.lower() for word in ["home", "ddecor"])]
    if home_fabrics:
        print(f"   Fabrics with 'HOME' or 'DDECOR':")
        for fabric in home_fabrics[:5]:
            print(f"      - {fabric.material_name} | Rs.{fabric.default_purchase_price}")
    
    # Show some random sample fabrics
    print(f"   Random Sample Fabrics:")
    import random
    sample_fabrics = random.sample(db_fabrics, min(10, len(db_fabrics)))
    for fabric in sample_fabrics:
        print(f"      - {fabric.material_name} | Rs.{fabric.default_purchase_price}")

if __name__ == "__main__":
    search_fabrics()
