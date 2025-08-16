#!/usr/bin/env python3
from test_basic_ocr import load_csv_fabrics

csv_fabrics = load_csv_fabrics()
royal_fabrics = [f for f in csv_fabrics if 'royal' in f['original_name'].lower()]

print(f'Found {len(royal_fabrics)} NEW ROYAL fabrics')
print('First 5:')
for f in royal_fabrics[:5]:
    print(f'  {f["original_name"]}')
