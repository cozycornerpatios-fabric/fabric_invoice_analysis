#!/usr/bin/env python3
"""
Robust Fabric Name Matcher
Matches fabric names extracted from invoices with database entries using multiple algorithms.
"""

import os
import re
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from pathlib import Path

# String matching libraries
from difflib import SequenceMatcher
import jellyfish
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Database connection
try:
    from supabase import create_client as _sb_create_client
except ImportError:
    _sb_create_client = None

# CSV fallback
import csv

# ========== Data Structures ==========
@dataclass
class ParsedFabric:
    """Fabric item extracted from invoice"""
    material_name: str
    quantity: float
    rate: float
    amount: float
    source_invoice: str

@dataclass
class DatabaseFabric:
    """Fabric item from database"""
    material_name: str
    default_purchase_price: float
    additional_fields: Dict = None

@dataclass
class MatchResult:
    """Result of fabric name matching"""
    parsed_fabric: ParsedFabric
    database_fabric: Optional[DatabaseFabric]
    match_score: float
    match_algorithm: str
    confidence_level: str  # "HIGH", "MEDIUM", "LOW", "NO_MATCH"
    suggested_price: Optional[float]
    price_difference: Optional[float]
    price_difference_percent: Optional[float]

# ========== String Normalization ==========
def normalize_string(s: str) -> str:
    """Normalize string for better matching"""
    if not s:
        return ""
    
    # Convert to lowercase
    s = s.lower()
    
    # Remove common noise patterns
    noise_patterns = [
        r'\b\d{1,2}\b',  # Single/double digit numbers
        r'\b5%\b',  # Tax percentages
        r'\b[A-Z]{2}\d{2}[A-Z]{5}\d{2}\b',  # HSN codes
        r'[^\w\s\-]',  # Remove punctuation except hyphens
        r'\s+',  # Multiple spaces
    ]
    
    for pattern in noise_patterns:
        s = re.sub(pattern, " ", s)
    
    # Clean up and normalize
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'^[-]+|[-]+$', '', s)
    
    return s

def tokenize_string(s: str) -> List[str]:
    """Tokenize string into meaningful words"""
    s = normalize_string(s)
    # Split and filter out very short tokens
    tokens = [token for token in s.split() if len(token) >= 2]
    return tokens

# ========== Matching Algorithms ==========
class FabricMatcher:
    """Robust fabric name matcher using multiple algorithms"""
    
    def __init__(self, database_fabrics: List[DatabaseFabric]):
        self.database_fabrics = database_fabrics
        self.db_index = self._build_index()
        
    def _build_index(self) -> Dict[str, DatabaseFabric]:
        """Build normalized index of database fabrics"""
        index = {}
        for fabric in self.database_fabrics:
            normalized = normalize_string(fabric.material_name)
            if normalized:
                index[normalized] = fabric
        return index
    
    def exact_match(self, parsed_name: str) -> Optional[Tuple[DatabaseFabric, float]]:
        """Exact string match"""
        normalized_parsed = normalize_string(parsed_name)
        if normalized_parsed in self.db_index:
            return self.db_index[normalized_parsed], 100.0
        return None
    
    def substring_match(self, parsed_name: str) -> Optional[Tuple[DatabaseFabric, float]]:
        """Check if parsed name is a substring of database name or vice versa"""
        normalized_parsed = normalize_string(parsed_name)
        parsed_tokens = set(tokenize_string(parsed_name))
        
        best_match = None
        best_score = 0.0
        
        for db_name, fabric in self.db_index.items():
            db_tokens = set(tokenize_string(db_name))
            
            # Enhanced substring matching for prefix-based naming
            # Check if parsed name is contained in database name (most common case)
            if normalized_parsed in db_name:
                # Calculate score based on how much of the parsed name matches
                match_ratio = len(normalized_parsed) / len(db_name)
                score = min(95.0, 80.0 + match_ratio * 20.0)
                if score > best_score:
                    best_score = score
                    best_match = fabric
                    print(f"      🔍 Substring match: '{normalized_parsed}' found in '{db_name}' (Score: {score:.1f}%)")
            
            # Check if database name (without prefix) is contained in parsed
            elif db_name in normalized_parsed:
                match_ratio = len(db_name) / len(normalized_parsed)
                score = min(95.0, 80.0 + match_ratio * 20.0)
                if score > best_score:
                    best_score = score
                    best_match = fabric
                    print(f"      🔍 Substring match: '{db_name}' found in '{normalized_parsed}' (Score: {score:.1f}%)")
            
            # Enhanced token overlap for prefix handling
            if parsed_tokens and db_tokens:
                # Remove common prefixes from database tokens for better matching
                db_tokens_clean = {token for token in db_tokens if not token in ['a', 'h', 's', 'home', 'ddecor', 'sujan']}
                
                # Calculate overlap with cleaned tokens
                overlap = len(parsed_tokens & db_tokens_clean)
                total = len(parsed_tokens | db_tokens_clean)
                
                if overlap > 0:
                    # Boost score for significant token overlap
                    token_score = (overlap / total) * 90.0
                    if token_score > best_score:
                        best_score = token_score
                        best_match = fabric
                        print(f"      🔍 Token overlap: {overlap}/{total} tokens match (Score: {token_score:.1f}%)")
        
        return (best_match, best_score) if best_score >= 60.0 else None
    
    def fuzzy_match(self, parsed_name: str) -> Optional[Tuple[DatabaseFabric, float]]:
        """Fuzzy string matching using multiple algorithms"""
        normalized_parsed = normalize_string(parsed_name)
        
        best_match = None
        best_score = 0.0
        
        for db_name, fabric in self.db_index.items():
            # SequenceMatcher (difflib)
            seq_score = SequenceMatcher(None, normalized_parsed, db_name).ratio() * 100
            
            # Jaro-Winkler distance
            jaro_score = jellyfish.jaro_winkler_similarity(normalized_parsed, db_name) * 100
            
            # Levenshtein distance
            lev_score = 100 - jellyfish.levenshtein_distance(normalized_parsed, db_name) / max(len(normalized_parsed), len(db_name)) * 100
            lev_score = max(0, lev_score)
            
            # FuzzyWuzzy ratios
            fuzz_ratio = fuzz.ratio(normalized_parsed, db_name)
            fuzz_partial = fuzz.partial_ratio(normalized_parsed, db_name)
            fuzz_token_sort = fuzz.token_sort_ratio(normalized_parsed, db_name)
            fuzz_token_set = fuzz.token_set_ratio(normalized_parsed, db_name)
            
            # Calculate weighted average
            scores = [seq_score, jaro_score, lev_score, fuzz_ratio, fuzz_partial, fuzz_token_sort, fuzz_token_set]
            avg_score = sum(scores) / len(scores)
            
            if avg_score > best_score:
                best_score = avg_score
                best_match = fabric
        
        return (best_match, best_score) if best_score >= 70.0 else None
    
    def semantic_match(self, parsed_name: str) -> Optional[Tuple[DatabaseFabric, float]]:
        """Semantic matching considering fabric type, color, pattern, etc."""
        normalized_parsed = normalize_string(parsed_name)
        parsed_tokens = tokenize_string(parsed_name)
        
        best_match = None
        best_score = 0.0
        
        # Define fabric-related keywords
        fabric_types = {'cotton', 'silk', 'wool', 'linen', 'polyester', 'rayon', 'nylon', 'acrylic'}
        colors = {'red', 'blue', 'green', 'yellow', 'black', 'white', 'brown', 'pink', 'purple', 'orange', 'gray', 'grey'}
        patterns = {'striped', 'checked', 'floral', 'geometric', 'solid', 'print', 'embroidery'}
        
        for db_name, fabric in self.db_index.items():
            db_tokens = tokenize_string(db_name)
            
            score = 0.0
            total_keywords = 0
            
            # Check fabric type matches
            for token in parsed_tokens:
                if token in fabric_types:
                    total_keywords += 1
                    if token in db_tokens:
                        score += 25.0
            
            # Check color matches
            for token in parsed_tokens:
                if token in colors:
                    total_keywords += 1
                    if token in db_tokens:
                        score += 20.0
            
            # Check pattern matches
            for token in parsed_tokens:
                if token in patterns:
                    total_keywords += 1
                    if token in db_tokens:
                        score += 15.0
            
            # Normalize score
            if total_keywords > 0:
                semantic_score = (score / total_keywords) * 100
                if semantic_score > best_score:
                    best_score = semantic_score
                    best_match = fabric
        
        return (best_match, best_score) if best_score >= 50.0 else None
    
    def prefix_based_match(self, parsed_name: str) -> Optional[Tuple[DatabaseFabric, float]]:
        """Special matching for prefix-based naming patterns like 'A - Agora', 'H - Home DDecor'"""
        normalized_parsed = normalize_string(parsed_name)
        parsed_tokens = set(tokenize_string(parsed_name))
        
        best_match = None
        best_score = 0.0
        
        # Common prefix patterns in your database
        prefix_patterns = [
            r'^[a-z]\s*-\s*',  # "A - ", "H - ", "S - "
            r'^[a-z]+\s*',     # "Home", "Sujan", "Agora"
        ]
        
        for db_name, fabric in self.db_index.items():
            db_tokens = set(tokenize_string(db_name))
            
            # Remove common prefixes for comparison
            db_name_clean = db_name
            for pattern in prefix_patterns:
                import re
                db_name_clean = re.sub(pattern, '', db_name_clean, flags=re.IGNORECASE)
            
            # Check if parsed name matches the cleaned database name
            if normalized_parsed in db_name_clean or db_name_clean in normalized_parsed:
                # High score for prefix-based matches
                match_ratio = len(normalized_parsed) / max(len(db_name_clean), len(normalized_parsed))
                score = min(95.0, 85.0 + match_ratio * 15.0)
                if score > best_score:
                    best_score = score
                    best_match = fabric
                    print(f"      🔍 Prefix match: '{normalized_parsed}' matches '{db_name_clean}' in '{db_name}' (Score: {score:.1f}%)")
            
            # Check for significant token overlap after removing prefixes
            if parsed_tokens and db_tokens:
                # Remove prefix tokens
                prefix_tokens = {'a', 'h', 's', 'home', 'ddecor', 'sujan', 'agora'}
                db_tokens_clean = {token for token in db_tokens if token.lower() not in prefix_tokens}
                
                if db_tokens_clean:
                    overlap = len(parsed_tokens & db_tokens_clean)
                    total = len(parsed_tokens | db_tokens_clean)
                    
                    if overlap >= 2:  # Require at least 2 tokens to match
                        token_score = (overlap / total) * 95.0
                        if token_score > best_score:
                            best_score = token_score
                            best_match = fabric
                            print(f"      🔍 Prefix token match: {overlap}/{total} tokens (Score: {token_score:.1f}%)")
        
        return (best_match, best_score) if best_score >= 70.0 else None
    
    def match_fabric(self, parsed_fabric: ParsedFabric) -> MatchResult:
        """Main matching function using all algorithms"""
        parsed_name = parsed_fabric.material_name
        
        # Try exact match first
        exact_result = self.exact_match(parsed_name)
        if exact_result:
            db_fabric, score = exact_result
            return self._create_match_result(parsed_fabric, db_fabric, score, "EXACT_MATCH", "HIGH")
        
        # Try prefix-based match (new algorithm for your database)
        prefix_result = self.prefix_based_match(parsed_name)
        if prefix_result:
            db_fabric, score = prefix_result
            confidence = "HIGH" if score >= 85.0 else "MEDIUM"
            return self._create_match_result(parsed_fabric, db_fabric, score, "PREFIX_BASED_MATCH", confidence)
        
        # Try substring match
        substring_result = self.substring_match(parsed_name)
        if substring_result:
            db_fabric, score = substring_result
            confidence = "HIGH" if score >= 85.0 else "MEDIUM"
            return self._create_match_result(parsed_fabric, db_fabric, score, "SUBSTRING_MATCH", confidence)
        
        # Try fuzzy match
        fuzzy_result = self.fuzzy_match(parsed_name)
        if fuzzy_result:
            db_fabric, score = fuzzy_result
            confidence = "HIGH" if score >= 85.0 else "MEDIUM"
            return self._create_match_result(parsed_fabric, db_fabric, score, "FUZZY_MATCH", confidence)
        
        # Try semantic match
        semantic_result = self.semantic_match(parsed_name)
        if semantic_result:
            db_fabric, score = semantic_result
            confidence = "MEDIUM" if score >= 70.0 else "LOW"
            return self._create_match_result(parsed_fabric, db_fabric, score, "SEMANTIC_MATCH", confidence)
        
        # No match found
        return self._create_match_result(parsed_fabric, None, 0.0, "NO_MATCH", "NO_MATCH")
    
    def _create_match_result(self, parsed_fabric: ParsedFabric, db_fabric: Optional[DatabaseFabric], 
                           score: float, algorithm: str, confidence: str) -> MatchResult:
        """Create match result with calculated metrics"""
        suggested_price = db_fabric.default_purchase_price if db_fabric else None
        price_difference = None
        price_difference_percent = None
        
        if suggested_price and parsed_fabric.rate:
            price_difference = abs(parsed_fabric.rate - suggested_price)
            price_difference_percent = (price_difference / suggested_price) * 100
        
        return MatchResult(
            parsed_fabric=parsed_fabric,
            database_fabric=db_fabric,
            match_score=score,
            match_algorithm=algorithm,
            confidence_level=confidence,
            suggested_price=suggested_price,
            price_difference=price_difference,
            price_difference_percent=price_difference_percent
        )

# ========== Database Functions ==========
def load_database_fabrics() -> List[DatabaseFabric]:
    """Load fabric data from database or CSV"""
    table = os.getenv("DB_TABLE", "materials_stage")
    fabrics = []
    
    # Try Supabase first
    sb_url = os.getenv("SUPABASE_URL")
    sb_key = os.getenv("SUPABASE_KEY")
    
    if sb_url and sb_key and _sb_create_client:
        try:
            print("🔗 Connecting to Supabase...")
            sb = _sb_create_client(sb_url, sb_key)
            res = sb.table(table).select("*").execute()
            
            for row in (res.data or []):
                material_name = row.get("material_name", "").strip()
                default_price = row.get("default_purchase_price")
                
                if material_name and default_price:
                    additional_fields = {k: v for k, v in row.items() 
                                       if k not in ["material_name", "default_purchase_price"]}
                    
                    fabrics.append(DatabaseFabric(
                        material_name=material_name,
                        default_purchase_price=float(default_price),
                        additional_fields=additional_fields
                    ))
            
            print(f"✅ Loaded {len(fabrics)} fabrics from Supabase")
            return fabrics
            
        except Exception as e:
            print(f"⚠️ Supabase load failed: {e}")
    
    # Fallback to CSV
    csv_path = os.getenv("INVENTORY_CSV")
    if csv_path and Path(csv_path).exists():
        try:
            print("📁 Loading from CSV fallback...")
            with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    material_name = row.get("material_name", "").strip()
                    default_price = row.get("default_purchase_price")
                    
                    if material_name and default_price:
                        try:
                            fabrics.append(DatabaseFabric(
                                material_name=material_name,
                                default_purchase_price=float(default_price),
                                additional_fields={}
                            ))
                        except ValueError:
                            continue
            
            print(f"✅ Loaded {len(fabrics)} fabrics from CSV")
            return fabrics
            
        except Exception as e:
            print(f"⚠️ CSV load failed: {e}")
    
    print("❌ No database connection available")
    return []

# ========== Main Function ==========
def main():
    """Main function to demonstrate fabric matching"""
    print("🔍 Fabric Name Matcher")
    print("=" * 50)
    
    # Load database fabrics
    db_fabrics = load_database_fabrics()
    if not db_fabrics:
        print("❌ No database fabrics loaded. Please check your configuration.")
        return
    
    # Initialize matcher
    matcher = FabricMatcher(db_fabrics)
    
    # Example parsed fabrics (you can replace these with actual parsed data)
    example_fabrics = [
        ParsedFabric("NEW ROYAL", 3.9, 549.0, 2141.1, "Home Ideas DDecor"),
        ParsedFabric("Agora 3787 Rayure Biege", 1.4, 1250.0, 1750.0, "Sujan Impex"),
        ParsedFabric("CASSIA - 101", 4.15, 720.0, 2988.0, "Sarom"),
        ParsedFabric("ALESIA-711", 2.4, 675.0, 1417.5, "Sarom"),
        ParsedFabric("KEIBA -912", 1.85, 570.0, 1054.5, "Sarom"),
    ]
    
    print(f"\n📊 Matching {len(example_fabrics)} parsed fabrics against {len(db_fabrics)} database entries...")
    print("-" * 80)
    
    # Match each fabric
    for fabric in example_fabrics:
        result = matcher.match_fabric(fabric)
        
        print(f"\n🔍 {fabric.material_name} (from {fabric.source_invoice})")
        print(f"   📏 Qty: {fabric.quantity}, Rate: ₹{fabric.rate}, Amount: ₹{fabric.amount}")
        
        if result.database_fabric:
            print(f"   ✅ MATCH: {result.database_fabric.material_name}")
            print(f"   🎯 Algorithm: {result.match_algorithm}")
            print(f"   📊 Score: {result.match_score:.1f}%")
            print(f"   🏷️ Confidence: {result.confidence_level}")
            print(f"   💰 DB Price: ₹{result.database_fabric.default_purchase_price}")
            
            if result.price_difference:
                print(f"   📈 Price Diff: ₹{result.price_difference:.2f} ({result.price_difference_percent:.1f}%)")
                
                if result.price_difference_percent <= 5:
                    print("   🟢 Price within 5% tolerance")
                elif result.price_difference_percent <= 15:
                    print("   🟡 Price within 15% tolerance")
                else:
                    print("   🔴 Price difference > 15%")
        else:
            print(f"   ❌ NO MATCH FOUND")
            print(f"   📊 Best Score: {result.match_score:.1f}%")
    
    print("\n" + "=" * 80)
    print("🎯 Matching Complete!")

if __name__ == "__main__":
    main()
