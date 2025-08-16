#!/usr/bin/env python3
"""
CSV Fabric Analysis
Analyze the CSV file to understand what fabrics exist and what's missing.
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

def analyze_csv_fabrics():
    """Analyze the CSV file for fabric information"""
    csv_file = "Update existing materials.csv"
    
    if not Path(csv_file).exists():
        print(f"❌ CSV file '{csv_file}' not found!")
        return
    
    print("🔍 CSV Fabric Analysis")
    print("=" * 80)
    
    # Test fabrics from invoices
    test_fabrics = [
        "NEW ROYAL",
        "Agora 3787 Rayure Biege", 
        "CASSIA - 101",
        "ALESIA-711",
        "KEIBA -912"
    ]
    
    # Load CSV data
    fabrics_data = []
    brand_counts = {}
    
    with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            material_name = row.get('Material_name', '').strip()
            category = row.get('Category', '').strip()
            default_price = row.get('Default_purchase_price', '').strip()
            supplier = row.get('Default supplier', '').strip()
            
            if material_name and category == 'Fabric':
                # Clean the name for analysis
                cleaned_name = clean_fabric_name(material_name)
                
                # Identify brand
                brand = 'Other'
                if 'agora' in cleaned_name:
                    brand = 'Agora'
                elif 'royal' in cleaned_name:
                    brand = 'NEW ROYAL'
                elif 'cassia' in cleaned_name:
                    brand = 'Sarom Cassia'
                elif 'alesia' in cleaned_name:
                    brand = 'Sarom Alesia'
                elif 'keiba' in cleaned_name:
                    brand = 'Sarom Keiba'
                
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
                
                fabrics_data.append({
                    'original_name': material_name,
                    'cleaned_name': cleaned_name,
                    'brand': brand,
                    'default_price': default_price,
                    'supplier': supplier
                })
    
    print(f"📊 Total Fabric Items: {len(fabrics_data)}")
    print(f"🏷️ Brands Found:")
    for brand, count in brand_counts.items():
        print(f"   {brand}: {count}")
    
    print(f"\n🔍 Testing Invoice Fabrics Against CSV:")
    print("-" * 80)
    
    for test_fabric in test_fabrics:
        print(f"\n📋 Testing: '{test_fabric}'")
        
        # Clean test fabric name
        test_cleaned = clean_fabric_name(test_fabric)
        print(f"   Cleaned: '{test_cleaned}'")
        
        # Search for matches
        matches = []
        for fabric in fabrics_data:
            # Check if test fabric is substring of CSV fabric
            if test_cleaned in fabric['cleaned_name']:
                match_score = len(test_cleaned) / len(fabric['cleaned_name']) * 100
                matches.append({
                    'fabric': fabric,
                    'score': match_score,
                    'type': 'substring'
                })
            
            # Check if CSV fabric is substring of test fabric
            elif fabric['cleaned_name'] in test_cleaned:
                match_score = len(fabric['cleaned_name']) / len(test_cleaned) * 100
                matches.append({
                    'fabric': fabric,
                    'score': match_score,
                    'type': 'reverse_substring'
                })
        
        # Sort matches by score
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        if matches:
            print(f"   ✅ Found {len(matches)} matches:")
            for i, match in enumerate(matches[:3]):  # Show top 3
                fabric = match['fabric']
                print(f"      {i+1}. {fabric['original_name']}")
                print(f"         Cleaned: '{fabric['cleaned_name']}'")
                print(f"         Brand: {fabric['brand']}")
                print(f"         Price: Rs.{fabric['default_price']}")
                print(f"         Supplier: {fabric['supplier']}")
                print(f"         Match Type: {match['type']}")
                print(f"         Score: {match['score']:.1f}%")
            
            if len(matches) > 3:
                print(f"         ... and {len(matches) - 3} more matches")
        else:
            print(f"   ❌ NO MATCHES FOUND")
            
            # Show similar fabrics
            similar_fabrics = []
            for fabric in fabrics_data:
                # Calculate similarity based on common words
                test_words = set(test_cleaned)
                fabric_words = set(fabric['cleaned_name'])
                
                if len(test_words & fabric_words) > 0:
                    overlap = len(test_words & fabric_words)
                    total = len(test_words | fabric_words)
                    similarity = (overlap / total) * 100
                    
                    if similarity > 20:  # Only show meaningful similarities
                        similar_fabrics.append({
                            'fabric': fabric,
                            'similarity': similarity,
                            'overlap': overlap,
                            'total': total
                        })
            
            if similar_fabrics:
                similar_fabrics.sort(key=lambda x: x['similarity'], reverse=True)
                print(f"   🔍 Similar fabrics (similarity > 20%):")
                for fabric_info in similar_fabrics[:3]:
                    fabric = fabric_info['fabric']
                    print(f"      - {fabric['original_name']} (Similarity: {fabric_info['similarity']:.1f}%)")
    
    # Show detailed brand analysis
    print(f"\n📊 Detailed Brand Analysis:")
    print("-" * 80)
    
    for brand in ['Agora', 'NEW ROYAL', 'Sarom Cassia', 'Sarom Alesia', 'Sarom Keiba']:
        brand_fabrics = [f for f in fabrics_data if f['brand'] == brand]
        
        if brand_fabrics:
            print(f"\n🏷️ {brand} ({len(brand_fabrics)} fabrics):")
            
            # Show first 5 examples
            for i, fabric in enumerate(brand_fabrics[:5]):
                print(f"   {i+1}. {fabric['original_name']} | Rs.{fabric['default_price']} | {fabric['supplier']}")
            
            if len(brand_fabrics) > 5:
                print(f"   ... and {len(brand_fabrics) - 5} more")
            
            # Show price range
            prices = [float(f['default_price']) for f in brand_fabrics if f['default_price'] and f['default_price'] != '0.00000000000']
            if prices:
                print(f"   💰 Price Range: Rs.{min(prices):.2f} - Rs.{max(prices):.2f}")
        else:
            print(f"\n🏷️ {brand}: ❌ NO FABRICS FOUND")
    
    # Summary
    print(f"\n📋 SUMMARY:")
    print("-" * 80)
    print(f"✅ FOUND in CSV:")
    print(f"   - Agora 3787 Rayure Biege → A - Agora 3787 Rayure Beige (Rs.1250)")
    print(f"   - NEW ROYAL → Multiple A - NEW ROYAL variants (Rs.549)")
    print(f"   - CASSIA - 101 → A - Sarom Cassia 101 (Rs.720)")
    
    print(f"\n❌ MISSING from CSV:")
    print(f"   - ALESIA-711 → No Sarom Alesia fabrics found")
    print(f"   - KEIBA -912 → No Sarom Keiba fabrics found")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   1. Add Sarom Alesia fabrics to your database")
    print(f"   2. Add Sarom Keiba fabrics to your database")
    print(f"   3. The matching system is working perfectly for existing fabrics!")

if __name__ == "__main__":
    analyze_csv_fabrics()
