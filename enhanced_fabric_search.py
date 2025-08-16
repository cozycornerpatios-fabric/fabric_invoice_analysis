#!/usr/bin/env python3
"""
Enhanced Fabric Search
Case-insensitive, space-removed substring search for fabric names.
"""

import csv
import re
from pathlib import Path

def clean_fabric_name(name: str) -> str:
    """Clean fabric name by removing spaces, making lowercase, removing punctuation"""
    if not name:
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove all spaces
    name = name.replace(" ", "")
    
    # Remove common punctuation except numbers
    name = re.sub(r'[^\w\d]', '', name)
    
    return name

def extract_fabric_info(parsed_name: str) -> dict:
    """Extract fabric brand, name, and number from parsed name"""
    cleaned = clean_fabric_name(parsed_name)
    
    # Try to identify fabric brand
    brands = {
        'agora': 'agora',
        'sarom': 'sarom', 
        'homeddecor': 'homeddecor',
        'home': 'homeddecor',
        'ddecor': 'homeddecor',
        'sujan': 'sujan',
        'royal': 'royal',
        'cassia': 'cassia',
        'alesia': 'alesia',
        'keiba': 'keiba'
    }
    
    brand_found = None
    for brand_key, brand_name in brands.items():
        if brand_key in cleaned:
            brand_found = brand_name
            break
    
    # Extract numbers (fabric codes)
    numbers = re.findall(r'\d+', cleaned)
    
    return {
        'original': parsed_name,
        'cleaned': cleaned,
        'brand': brand_found,
        'numbers': numbers,
        'has_brand': brand_found is not None
    }

def search_fabric_database():
    """Enhanced search with case-insensitive, space-removed substring matching"""
    print("Enhanced Fabric Search - CSV Analysis")
    print("=" * 70)
    
    # Load CSV data
    csv_file = "Update existing materials.csv"
    if not Path(csv_file).exists():
        print(f"❌ CSV file '{csv_file}' not found!")
        return
    
    fabrics_data = []
    with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            material_name = row.get('Material_name', '').strip()
            category = row.get('Category', '').strip()
            default_price = row.get('Default_purchase_price', '').strip()
            supplier = row.get('Default supplier', '').strip()
            
            if material_name and category == 'Fabric':
                cleaned_name = clean_fabric_name(material_name)
                fabrics_data.append({
                    'original_name': material_name,
                    'cleaned_name': cleaned_name,
                    'default_price': default_price,
                    'supplier': supplier
                })
    
    print(f"📊 Loaded {len(fabrics_data)} fabrics from CSV")
    
    # Test fabrics from invoices
    test_fabrics = [
        "NEW ROYAL",
        "Agora 3787 Rayure Biege", 
        "CASSIA - 101",
        "ALESIA-711",
        "KEIBA -912"
    ]
    
    print(f"\nTesting {len(test_fabrics)} fabric names:")
    print("-" * 70)
    
    for fabric_name in test_fabrics:
        print(f"\nSearching for: '{fabric_name}'")
        
        # Extract fabric info
        fabric_info = extract_fabric_info(fabric_name)
        print(f"   Cleaned: '{fabric_info['cleaned']}'")
        print(f"   Brand: {fabric_info['brand'] or 'Unknown'}")
        print(f"   Numbers: {fabric_info['numbers']}")
        
        # Search in CSV database
        matches = []
        for fabric in fabrics_data:
            db_cleaned = fabric['cleaned_name']
            
            # Check if cleaned parsed name is substring of cleaned CSV name
            if fabric_info['cleaned'] in db_cleaned:
                match_score = len(fabric_info['cleaned']) / len(db_cleaned) * 100
                matches.append({
                    'fabric': fabric,
                    'db_cleaned': db_cleaned,
                    'score': match_score,
                    'type': 'substring'
                })
            
            # Check if cleaned CSV name is substring of cleaned parsed name
            elif db_cleaned in fabric_info['cleaned']:
                match_score = len(db_cleaned) / len(fabric_info['cleaned']) * 100
                matches.append({
                    'fabric': fabric,
                    'db_cleaned': db_cleaned,
                    'score': match_score,
                    'type': 'reverse_substring'
                })
        
        # Sort matches by score
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        if matches:
            print(f"   ✅ Found {len(matches)} matches:")
            for i, match in enumerate(matches[:5]):  # Show top 5
                fabric = match['fabric']
                print(f"      {i+1}. {fabric['original_name']}")
                print(f"         Cleaned: '{match['db_cleaned']}'")
                print(f"         Score: {match['score']:.1f}%")
                print(f"         Price: Rs.{fabric['default_price']}")
                print(f"         Supplier: {fabric['supplier']}")
                print(f"         Match Type: {match['type']}")
            
            if len(matches) > 5:
                print(f"         ... and {len(matches) - 5} more matches")
        else:
            print(f"   ❌ No matches found")
            
            # Try partial matching
            print(f"   🔍 Trying partial matching...")
            partial_matches = []
            
            for fabric in fabrics_data:
                db_cleaned = fabric['cleaned_name']
                
                # Check for any word overlap
                parsed_words = set(fabric_info['cleaned'])
                db_words = set(db_cleaned)
                
                if len(parsed_words & db_words) > 0:
                    overlap = len(parsed_words & db_words)
                    total = len(parsed_words | db_words)
                    partial_score = (overlap / total) * 100
                    
                    if partial_score > 20:  # Only show meaningful partial matches
                        partial_matches.append({
                            'fabric': fabric,
                            'db_cleaned': db_cleaned,
                            'score': partial_score,
                            'overlap': overlap,
                            'total': total
                        })
            
            if partial_matches:
                partial_matches.sort(key=lambda x: x['score'], reverse=True)
                print(f"      Found {len(partial_matches)} partial matches:")
                for match in partial_matches[:3]:
                    print(f"         - {match['fabric']['original_name']} (Score: {match['score']:.1f}%)")
    
    # Show database statistics
    print(f"\nDatabase Analysis:")
    print("-" * 70)
    
    # Count fabrics by brand
    brand_counts = {}
    for fabric in fabrics_data:
        cleaned = fabric['cleaned_name']
        
        if 'agora' in cleaned:
            brand_counts['Agora'] = brand_counts.get('Agora', 0) + 1
        elif 'royal' in cleaned:
            brand_counts['NEW ROYAL'] = brand_counts.get('NEW ROYAL', 0) + 1
        elif 'cassia' in cleaned:
            brand_counts['Sarom Cassia'] = brand_counts.get('Sarom Cassia', 0) + 1
        elif 'alesia' in cleaned:
            brand_counts['Sarom Alesia'] = brand_counts.get('Sarom Alesia', 0) + 1
        elif 'keiba' in cleaned:
            brand_counts['Sarom Keiba'] = brand_counts.get('Sarom Keiba', 0) + 1
        else:
            brand_counts['Other'] = brand_counts.get('Other', 0) + 1
    
    print("Fabrics by brand:")
    for brand, count in brand_counts.items():
        print(f"   {brand}: {count}")
    
    # Show some examples of each brand
    print(f"\nSample fabrics by brand:")
    for brand in ['Agora', 'NEW ROYAL', 'Sarom Cassia', 'Sarom Alesia', 'Sarom Keiba']:
        brand_fabrics = []
        for fabric in fabrics_data:
            cleaned = fabric['cleaned_name']
            if brand.lower().replace(' ', '') in cleaned:
                brand_fabrics.append(fabric)
                if len(brand_fabrics) >= 3:  # Show 3 examples
                    break
        
        if brand_fabrics:
            print(f"\n   {brand}:")
            for fabric in brand_fabrics:
                print(f"      - {fabric['original_name']} | Rs.{fabric['default_price']}")

if __name__ == "__main__":
    search_fabric_database()
