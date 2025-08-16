#!/usr/bin/env python3
from test_basic_ocr import clean_fabric_name, remove_csv_prefix, find_csv_fabric_match, load_csv_fabrics

csv_fabrics = load_csv_fabrics()
royal_fabrics = [f for f in csv_fabrics if 'royal' in f['original_name'].lower()]

print(f'Found {len(royal_fabrics)} NEW ROYAL fabrics')

# Test with first NEW ROYAL fabric
test_fabric = "NEW ROYAL"
test_cleaned = clean_fabric_name(test_fabric)
print(f'\nTesting: "{test_fabric}" -> "{test_cleaned}"')

# Check first few NEW ROYAL fabrics
print('\nFirst 3 NEW ROYAL fabrics:')
for i, fabric in enumerate(royal_fabrics[:3]):
    csv_name = fabric['original_name']
    csv_cleaned = fabric['cleaned_name']
    csv_no_prefix = remove_csv_prefix(csv_name)
    csv_no_prefix_cleaned = clean_fabric_name(csv_no_prefix)
    
    print(f'  {i+1}. Original: "{csv_name}"')
    print(f'     No Prefix: "{csv_no_prefix}"')
    print(f'     No Prefix Cleaned: "{csv_no_prefix_cleaned}"')
    
    # Check substring matching
    if test_cleaned in csv_no_prefix_cleaned:
        print(f'     ✅ SUBSTRING MATCH!')
        match_score = len(test_cleaned) / len(csv_no_prefix_cleaned) * 100
        print(f'     Score: {match_score:.1f}%')
    else:
        print(f'     ❌ No substring match')

# Test the matching function
print(f'\nTesting find_csv_fabric_match:')
match = find_csv_fabric_match(test_fabric, csv_fabrics)
print(f'Match found: {match is not None}')
if match:
    print(f'Match details: {match}')
else:
    print('No match found - this indicates a bug in the matching function')
