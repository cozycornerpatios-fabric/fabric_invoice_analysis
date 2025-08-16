#!/usr/bin/env python3
"""
Invoice (name, qty, amount) → rate := amount/qty → compare with DB default_purchase_price.

DB schema expected (Supabase table default: materials_stage):
  - material_name
  - default_purchase_price

Env:
  TESSERACT_CMD=/usr/bin/tesseract              # if tesseract isn't on PATH
  SUPABASE_URL=...
  SUPABASE_KEY=...
  DB_TABLE=materials_stage
  INVENTORY_CSV=/path/to/fallback.csv           # cols: material_name, default_purchase_price
  RATE_TOLERANCE_PCT=0.10                       # ±10% default
"""

import os, re, sys, csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Dict

# --- OCR / PDF ---
import fitz  # PyMuPDF
import cv2, numpy as np
from PIL import Image
import pytesseract

# --- Supabase (optional) ---
try:
    from supabase import create_client as _sb_create_client  # type: ignore
except Exception:
    _sb_create_client = None

# --- CSV Fabric Matching ---
from difflib import SequenceMatcher


@dataclass
class TaxLine:
    tax: str                     # "IGST"
    rate_pct: Optional[float]    # e.g., 5.0
    amount: Optional[float]      # e.g., 142.76
    line_text: str               # the original line (for debugging)


@dataclass
class TaxSummary:
    gst_rate: Optional[float] = None  # e.g., 5.0 for 5%
    cgst: Optional[float] = None
    sgst: Optional[float] = None


@dataclass
class OutputIGST:
    label: str
    amount: Optional[float]
    line_text: str


@dataclass
class HomeIdeasTotals:
    sub_total: Optional[float] = None
    courier_charges: Optional[float] = None
    add_charges: Optional[float] = None
    taxable_value: Optional[float] = None
    tcs_amount: Optional[float] = None
    igst_amount: Optional[float] = None
    cgst_amount: Optional[float] = None
    sgst_amount: Optional[float] = None
    total_inc_taxes: Optional[float] = None


def _fmt_money(v: Optional[float]) -> str:
    return f"₹{v:.2f}" if v is not None else "—"


# ========== util ==========
def _wire_tesseract():
    tcmd = os.getenv("TESSERACT_CMD") or os.getenv("PYTESSERACT_CMD")
    if tcmd:
        pytesseract.pytesseract.tesseract_cmd = tcmd

def _norm(s: str) -> str:
    s = re.sub(r"[\s_]+", " ", s or "").strip().lower()
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    return re.sub(r"\s+", " ", s)

def _num(x) -> Optional[float]:
    if x is None: return None
    s = re.sub(r"[^\d.]", "", str(x).replace(",", ""))
    try: return float(s) if s else None
    except: return None

def _clean_name(desc: str) -> str:
    if not desc: return ""
    
    # Remove common invoice noise
    desc = re.sub(r"\s*\([^)]*\)|\s*\[[^\]]*\]", "", desc)
    
    # Remove specific patterns found in Sarom.pdf
    noise = [
        r"\b(GSTIN|GST|IGST|CGST|SGST|Tax|Total|Sub[- ]?total|Grand Total|Invoice|Bill|Address|Ship To|PIN|Pincode|Phone|Mobile|Email)\b",
        r"[A-Z]{2}\d{2}[A-Z]{5}\d[A-Z]\d[A-Z]\d",  # GSTIN-like
        r"\b\d{6}\b",
        r"\b\d{1,2}\b",  # Single/double digit numbers (like line numbers)
        r"\b5%\b",  # Tax percentages
        r"\b[A-Z]{2}\d{2}[A-Z]{5}\d{2}\b",  # HSN codes like 55169200
        r"\b[A-Z]{2}\d{2}[A-Z]{5}\d{2}\b",  # HSN codes like 55169200
        r"\|\s*5%\s*\|",  # Tax percentage patterns
        r"\|\s*5%:",  # Tax percentage patterns
        r"\|\s*5%!",  # Tax percentage patterns
        r"\|\s*5%\)",  # Tax percentage patterns
        r"\|\s*5%i",  # Tax percentage patterns
        r"§\d+",  # Section symbols with numbers
        r"\$\d+",  # Dollar symbols with numbers
        r"\"\d+",  # Quote symbols with numbers
        r"~\d+",  # Tilde symbols with numbers
        r"-\d+",  # Dash with numbers
    ]
    
    for p in noise: 
        desc = re.sub(p, "", desc, flags=re.I)
    
    # Clean up extra whitespace and normalize
    desc = re.sub(r"\s+", " ", desc).strip()
    
    # Remove leading/trailing punctuation and symbols
    desc = re.sub(r"^[:\-\s|]+|[:\-\s|]+$", "", desc)
    
    # If description is too short or contains mostly numbers/symbols, return empty
    if len(desc) < 3 or re.fullmatch(r"[₹\d\s\.,/-]+", desc): 
        return ""
    
    return desc

def _token_set_ratio(a: str, b: str) -> float:
    ta, tb = set(_norm(a).split()), set(_norm(b).split())
    if not ta or not tb: return 0.0
    inter, union = ta & tb, ta | tb
    j = len(inter) / len(union)
    if _norm(a) in _norm(b) or _norm(b) in _norm(a): j = max(j, 0.85)
    return round(100 * j, 2)

# ========== CSV Fabric Matching ==========
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

def remove_csv_prefix(name: str) -> str:
    """Remove common CSV prefixes like 'A - '"""
    # Remove "A - " prefix
    if name.startswith("A - "):
        return name[4:]
    return name

def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate string similarity using multiple methods"""
    # SequenceMatcher similarity
    seq_similarity = SequenceMatcher(None, str1, str2).ratio()
    
    # Character overlap similarity
    char_overlap = len(set(str1) & set(str2)) / len(set(str1) | set(str2)) if str1 and str2 else 0
    
    # Word overlap similarity (if we can split)
    word_similarity = 0
    if ' ' in str1 and ' ' in str2:
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        if words1 and words2:
            word_overlap = len(words1 & words2) / len(words1 | words2)
            word_similarity = word_overlap
    
    # Weighted average
    return (seq_similarity * 0.5 + char_overlap * 0.3 + word_similarity * 0.2)

def find_csv_fabric_match(parsed_name: str, csv_fabrics: list, threshold: float = 0.5) -> Optional[dict]:
    """Find best CSV fabric match using multiple matching strategies"""
    if not csv_fabrics:
        return None
    
    # Clean parsed name
    parsed_cleaned = clean_fabric_name(parsed_name)
    
    best_match = None
    best_score = 0.0
    
    for fabric in csv_fabrics:
        csv_name = fabric['original_name']
        csv_cleaned = fabric['cleaned_name']
        
        # Remove CSV prefix for comparison
        csv_name_no_prefix = remove_csv_prefix(csv_name)
        csv_cleaned_no_prefix = clean_fabric_name(csv_name_no_prefix)
        
        # Strategy 1: Direct substring matching (after removing CSV prefix)
        if parsed_cleaned in csv_cleaned_no_prefix:
            # Boost score for short fabric names that are found as substrings
            base_score = len(parsed_cleaned) / len(csv_cleaned_no_prefix) * 100
            if len(parsed_cleaned) <= 10:
                # For short names like "NEW ROYAL", boost the score significantly
                match_score = min(95.0, base_score + 60.0)
            else:
                match_score = base_score
            
            if match_score > best_score:
                best_score = match_score
                best_match = {
                    'fabric': fabric,
                    'csv_name_no_prefix': csv_name_no_prefix,
                    'csv_cleaned_no_prefix': csv_cleaned_no_prefix,
                    'score': match_score,
                    'method': 'Direct Substring (No Prefix)'
                }
        
        # Strategy 2: CSV name (without prefix) is substring of parsed name
        elif csv_cleaned_no_prefix in parsed_cleaned:
            match_score = len(csv_cleaned_no_prefix) / len(parsed_cleaned) * 100
            if match_score > best_score:
                best_score = match_score
                best_match = {
                    'fabric': fabric,
                    'csv_name_no_prefix': csv_name_no_prefix,
                    'csv_cleaned_no_prefix': csv_cleaned_no_prefix,
                    'score': match_score,
                    'method': 'Reverse Substring (No Prefix)'
                }
        
        # Strategy 3: Fuzzy matching with similarity threshold
        similarity = calculate_similarity(parsed_cleaned, csv_cleaned_no_prefix)
        if similarity >= threshold:
            fuzzy_score = similarity * 100
            if fuzzy_score > best_score:
                best_score = fuzzy_score
                best_match = {
                    'fabric': fabric,
                    'csv_name_no_prefix': csv_name_no_prefix,
                    'csv_cleaned_no_prefix': csv_cleaned_no_prefix,
                    'score': fuzzy_score,
                    'method': f'Fuzzy Match (Similarity: {similarity:.2f})'
                }
    
    # For short fabric names (like "NEW ROYAL"), lower the threshold
    min_threshold = 30.0 if len(parsed_cleaned) <= 10 else 50.0
    return best_match if best_score >= min_threshold else None

def load_csv_fabrics() -> list:
    """Load fabric data from CSV file"""
    csv_file = "Update existing materials.csv"
    fabrics_data = []
    
    if not Path(csv_file).exists():
        print(f"⚠️ CSV file '{csv_file}' not found, using empty fabric database")
        return fabrics_data
    
    try:
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
        
        print(f"✅ Loaded {len(fabrics_data)} fabrics from CSV")
        return fabrics_data
        
    except Exception as e:
        print(f"⚠️ Error loading CSV: {e}")
        return fabrics_data


# ========== DB ==========
@dataclass
class DBItem:
    material_name: str
    default_purchase_price: Optional[float]

def load_db_items() -> List[DBItem]:
    table = os.getenv("DB_TABLE", "materials_stage")
    items: List[DBItem] = []

    sb_url = os.getenv("SUPABASE_URL")
    sb_key = os.getenv("SUPABASE_KEY")
    if sb_url and sb_key and _sb_create_client:
        try:
            sb = _sb_create_client(sb_url, sb_key)
            res = sb.table(table).select("material_name,default_purchase_price").execute()
            for row in (res.data or []):
                nm = (row.get("material_name") or "").strip()
                if not nm: continue
                items.append(DBItem(nm, _num(row.get("default_purchase_price"))))
            if items: return items
        except Exception as e:
            print(f"⚠️ Supabase load failed: {e}")

    csv_path = os.getenv("INVENTORY_CSV") or os.getenv("INVENTORY_CSV_FALLBACK")
    if csv_path and Path(csv_path).exists():
        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            for row in csv.DictReader(f):
                nm = (row.get("material_name") or "").strip()
                if not nm: continue
                items.append(DBItem(nm, _num(row.get("default_purchase_price"))))
    return items

def build_db_index(db_items: List[DBItem]) -> Dict[str, DBItem]:
    return {_norm(x.material_name): x for x in db_items}

def best_match(name: str, db_index: Dict[str, DBItem]) -> Tuple[Optional[DBItem], float]:
    key = _norm(name)
    if key in db_index: return db_index[key], 100.0
    best, scbest = None, 0.0
    for k, it in db_index.items():
        sc = _token_set_ratio(key, k)
        if sc > scbest: scbest, best = sc, it
    return (best, scbest) if scbest >= 80.0 else (None, scbest)


# ========== OCR ==========
def _extract_text_from_pdf(path: str) -> str:
    """Try pdfplumber first for better table structure, fall back to fitz+OCR for scanned PDFs"""
    try:
        # Try pdfplumber first for better table structure preservation
        import pdfplumber
        txt_pages = []
        with pdfplumber.open(path) as pdf:
            for p in pdf.pages:
                # Use tolerance settings for better table extraction
                txt_pages.append(p.extract_text(x_tolerance=2, y_tolerance=3) or "")
        text = "\n".join(txt_pages).strip()
        
        # If pdfplumber extracted no meaningful text, it's likely a scanned PDF
        if not text or len(text) < 50:
            print("   📄 pdfplumber extracted minimal text, trying OCR approach...")
            raise Exception("No meaningful text from pdfplumber")
        
        return text
    except (ImportError, Exception):
        # Fall back to fitz + OCR for scanned PDFs
        try:
            print("   📄 Using PyMuPDF + OCR for scanned PDF...")
            doc = fitz.open(path)
            parts = []
            for i in range(len(doc)):
                page = doc.load_page(i)
                t = page.get_text().strip()
                if t and len(t) > 20:
                    parts.append(t)
                else:
                    # Convert page to image and use OCR
                    pix = page.get_pixmap(dpi=300, alpha=False)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
                    den = cv2.medianBlur(gray, 3)
                    thr = cv2.adaptiveThreshold(den, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                cv2.THRESH_BINARY, 31, 5)
                    ocr = pytesseract.image_to_string(thr, lang="eng")
                    if ocr.strip(): 
                        parts.append(ocr.strip())
                        print(f"      📄 Page {i+1}: OCR extracted {len(ocr.strip())} characters")
            doc.close()
            return "\n".join(parts).strip()
        except Exception as e:
            print(f"PDF extract error: {e}")
            return ""

def _extract_text_from_image(path: str) -> str:
    try:
        img = cv2.imread(path)
        if img is None: return ""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        den = cv2.medianBlur(gray, 3)
        thr = cv2.adaptiveThreshold(den, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 31, 5)
        return pytesseract.image_to_string(thr, lang="eng").strip()
    except Exception as e:
        print(f"Image OCR error: {e}")
        return ""

def extract_text(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext == ".pdf": return _extract_text_from_pdf(path)
    if ext in [".png",".jpg",".jpeg",".tif",".tiff",".bmp",".webp"]: return _extract_text_from_image(path)
    raise ValueError(f"Unsupported file type: {ext}")


def extract_igst_lines(text: str) -> List[TaxLine]:
    """
    Extract IGST lines (rate % and amount) from invoice text.
    Handles common OCR variants like 'lGST'/'1GST'/'I GST', and flexible formatting:
      - "IGST @ 5% 142.76"
      - "IGST 5% : ₹142.76"
      - "IGST (5%) ... 142.76"
      - "Total IGST Amount 142.76"
    Strategy:
      - Scan lines containing IGST token.
      - Grab first percentage in the line as rate.
      - Grab last currency-like number after the token as amount (fallback to neighbor lines).
    """
    igst_token = re.compile(r'\b[iI1l]\s*G\s*S\s*T\b', re.IGNORECASE)  # tolerant of OCR spacing
    pct_re     = re.compile(r'(\d{1,2}(?:\.\d{1,2})?)\s*%')            # 5 or 5.00%
    amt_re     = re.compile(r'₹?\s*([\d,]+(?:\.\d{1,2})?)')             # ₹1,234.56 or 1234.56

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out: List[TaxLine] = []

    for i, line in enumerate(lines):
        if not igst_token.search(line):
            # small heuristic: sometimes "I GST" is spaced weirdly; compress spaces then retry
            compact = re.sub(r'\s+', '', line, flags=re.I)
            if not re.search(r'[iI1l]GST', compact, re.I):
                continue

        # Try to read rate
        rate = None
        m_rate = pct_re.search(line)
        if m_rate:
            try:
                rate = float(m_rate.group(1))
            except Exception:
                rate = None

        # Try to read amount (prefer numbers AFTER the IGST token)
        amount = None
        tok = igst_token.search(line)
        post = line[tok.end():] if tok else line
        nums = amt_re.findall(post)
        if nums:
            try:
                amount = float(nums[-1].replace(',', ''))
            except Exception:
                amount = None
        else:
            # Fallback: check the next line (tables often wrap)
            if i + 1 < len(lines):
                nxt_nums = amt_re.findall(lines[i + 1])
                if nxt_nums:
                    try:
                        amount = float(nxt_nums[-1].replace(',', ''))
                    except Exception:
                        amount = None

        out.append(TaxLine(tax="IGST", rate_pct=rate, amount=amount, line_text=line))

    return out


def pick_invoice_igst(igst_lines: List[TaxLine]) -> Optional[TaxLine]:
    """
    Heuristic to select the 'invoice total' IGST when there are multiple matches.
    Picks the line with the largest non-None amount; if none have amounts,
    returns the last seen line.
    """
    if not igst_lines:
        return None
    with_amount = [t for t in igst_lines if t.amount is not None]
    if with_amount:
        return max(with_amount, key=lambda t: t.amount or 0)
    return igst_lines[-1]


def extract_cgst_sgst_roundoff(text: str) -> TaxSummary:
    """
    Pull CGST SALES, SGST SALES, and Rounded Off from Sarom-style invoices.
    Also detects the GST rate (e.g., 5%, 18%).
    Tolerant of OCR variants: 'C G S T', 'C.G.S.T', 'Round off', 'Rounded Off', 'R/O', etc.
    If amount is not on the same line, looks at the next 1–2 lines.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Amount matcher: ₹1,234.56 | 1234.56 | +0.48 | -0.48
    amt_re = re.compile(r'₹?\s*([+-]?\d[\d,]*(?:\.\d+)?)')
    
    # GST Rate matcher: 5%, 18%, 12% etc.
    gst_rate_re = re.compile(r'\b(\d{1,2}(?:\.\d{1,2})?)\s*%\s*(?:GST|Tax|Rate)?\b', re.I)

    def _grab_amount_from(i: int, start_col: int = 0) -> Optional[float]:
        # Try same line, after the matched label
        mlist = amt_re.findall(lines[i][start_col:])
        if mlist:
            return _num(mlist[-1])
        # Fallback: numbers on the next 1–2 lines (tables often wrap)
        for j in (1, 2):
            if i + j >= len(lines): break
            mlist = amt_re.findall(lines[i + j])
            if mlist:
                return _num(mlist[-1])
        return None

    def _find_amount_by_labels(patterns: List[re.Pattern]) -> Optional[float]:
        for i, ln in enumerate(lines):
            for pat in patterns:
                m = pat.search(ln)
                if m:
                    val = _grab_amount_from(i, m.end())
                    if val is not None:
                        return val
        return None
    
    def _find_gst_rate() -> Optional[float]:
        """Find GST rate percentage in the invoice text"""
        for ln in lines:
            m = gst_rate_re.search(ln)
            if m:
                try:
                    rate = float(m.group(1))
                    # Common GST rates in India: 5%, 12%, 18%, 28%
                    if rate in [5, 12, 18, 28] or (rate > 0 and rate <= 30):
                        return rate
                except ValueError:
                    continue
        return None

    cgst_patterns = [
        re.compile(r'\bC\.?\s*G\.?\s*S\.?\s*T\.?\s*(?:SALES|OUTPUT)?\b', re.I),
        re.compile(r'\bC\s*G\s*S\s*T\s*(?:SALES|OUTPUT)?\b', re.I),
    ]
    sgst_patterns = [
        re.compile(r'\bS\.?\s*G\.?\s*S\.?\s*T\.?\s*(?:SALES|OUTPUT)?\b', re.I),
        re.compile(r'\bS\s*G\s*S\s*T\s*(?:SALES|OUTPUT)?\b', re.I),
    ]

    return TaxSummary(
        gst_rate=_find_gst_rate(),
        cgst=_find_amount_by_labels(cgst_patterns),
        sgst=_find_amount_by_labels(sgst_patterns),
    )


def extract_output_igst_total(text: str) -> Optional[OutputIGST]:
    """
    Find 'Output IGST-Delhi' (or similar) in Sujan Impex invoices and return its amount.
    Robust to OCR: 'Output I GST', 'Output lGST', 'Output 1GST', hyphen/emdash, city suffix optional.
    If the amount isn't on the same line, checks the next 1–2 lines (common in table exports).
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # tolerant IGST token and "Output ..." label
    out_igst_pat = re.compile(
        r'\bOutput\s*[iI1l]\s*G\s*S\s*T\b(?:\s*[-–—]\s*[A-Za-z .]+)?',  # e.g., Output IGST-Delhi
        re.IGNORECASE,
    )
    amt_re = re.compile(r'₹?\s*([+-]?\d[\d,]*(?:\.\d+)?)')  # grabs right-aligned numbers like 347.51

    def grab_amount(i: int, start_col: int) -> Optional[float]:
        # Prefer numbers to the RIGHT of the matched label on the same line
        same_line_nums = amt_re.findall(lines[i][start_col:])
        if same_line_nums:
            return _num(same_line_nums[-1])
        # Fallback: next 1–2 lines (table wrapping)
        for j in (1, 2):
            if i + j >= len(lines): break
            nxt_nums = amt_re.findall(lines[i + j])
            if nxt_nums:
                return _num(nxt_nums[-1])
        # Rare fallback: previous line may hold the amount
        for j in (1, 2):
            if i - j < 0: break
            prv_nums = amt_re.findall(lines[i - j])
            if prv_nums:
                return _num(prv_nums[-1])
        return None

    hits: List[OutputIGST] = []
    for i, ln in enumerate(lines):
        m = out_igst_pat.search(ln)
        if not m:
            # Sometimes OCR collapses spaces; try compacted line
            compact = re.sub(r'\s+', '', ln)
            m = re.search(r'Output[iI1l]GST(?:[-–—][A-Za-z.]+)?', compact, re.I)
            if not m:
                continue
        amt = grab_amount(i, m.end())
        label = ln[m.start():m.end()]
        hits.append(OutputIGST(label=label, amount=amt, line_text=ln))

    if not hits:
        return None

    # If multiple matches (rare), choose the one with the largest amount
    with_amount = [h for h in hits if h.amount is not None]
    return max(with_amount, key=lambda h: h.amount or 0) if with_amount else hits[-1]


def extract_homeideas_totals(text: str) -> HomeIdeasTotals:
    """
    Extract the totals panel from Home Ideas / D'Decor invoices.
    Works when lines look like:
      Sub Total                18.20   9,991.80
      Courier Charges                   0.00
      IGST Amount                       499.60
      TOTAL INC. OF TAXES             10,491.40
    Strategy:
      - Find a label by regex (OCR tolerant).
      - Take the right-most numeric on the same line; else look on the next 1–2 lines.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Matches ₹1,234.56, 1234.56, +0.48, -0.48, etc.
    amt_re = re.compile(r'₹?\s*([+-]?\d[\d,]*(?:\.\d+)?)')

    def rightmost_amount_after(i: int, start_col: int = 0) -> Optional[float]:
        # Prefer numbers to the right of the label on the same line
        nums = amt_re.findall(lines[i][start_col:])
        if nums:
            return _num(nums[-1])

        # Fallback: amounts may wrap to next lines in OCR/text extraction
        for off in (1, 2):
            if i + off < len(lines):
                nums = amt_re.findall(lines[i + off])
                if nums:
                    return _num(nums[-1])
        return None

    def amount_for(patterns: List[re.Pattern]) -> Optional[float]:
        for i, ln in enumerate(lines):
            for p in patterns:
                m = p.search(ln)
                if m:
                    # Right-most number on/after the label
                    val = rightmost_amount_after(i, m.end())
                    if val is not None:
                        return val
        return None

    pats = {
        "sub_total": [
            re.compile(r'\bSub\s*Total\b', re.I),
            re.compile(r'\bSubtotal\b', re.I),
        ],
        "courier_charges": [
            re.compile(r'\bCourier\s*Charges?\b', re.I),
        ],
        "add_charges": [
            re.compile(r'\bAdd/?\s*Charges?\b', re.I),
            re.compile(r'\bAdd\.?\s*Charges?\b', re.I),
            re.compile(r'\bAdditional\s*Charges?\b', re.I),
        ],
        "taxable_value": [
            re.compile(r'\bTaxable\s*Value\b', re.I),
        ],
        "tcs_amount": [
            re.compile(r'\bTCS\s*Amount\b', re.I),
            re.compile(r'\bTCS\b', re.I),
        ],
        "igst_amount": [
            re.compile(r'\bIGST\s*Amount\b', re.I),
        ],
        "cgst_amount": [
            re.compile(r'\bCGST\s*Amount\b', re.I),
        ],
        "sgst_amount": [
            re.compile(r'\bSGST\s*Amount\b', re.I),
        ],
        "total_inc_taxes": [
            re.compile(r'\bTOTAL\s*INC\.?\s*OF\s*TAXES\b', re.I),
            re.compile(r'\bTotal\s*Incl?\.?\s*of\s*Taxes\b', re.I),
            re.compile(r'\bGrand\s*Total\b', re.I),  # occasional variant
        ],
    }

    values = {k: amount_for(v) for k, v in pats.items()}
    return HomeIdeasTotals(**values)


# ========== Parse (name, qty, amount → rate:=amount/qty) ==========
@dataclass
class InvoiceLine:
    material_name: str
    quantity: Optional[float]
    amount: Optional[float]
    rate: Optional[float]  # computed as amount/qty (preferred), else explicit rate

# ========== Universal Multi-Format Invoice Parser ==========
class UniversalInvoiceParser:
    """Universal parser that can handle multiple invoice formats automatically"""
    
    def __init__(self):
        self.format_patterns = {
            'sarom': {
                'indicators': ['SAROM', 'THAKOR IND ESTATE', 'VIDHYAVIHAR'],
                'item_pattern': r'(\d+(?:\.\d+)?)\s*(?:My|Mtr|Meter|Mtr,|Mtr~)\s*(\d+(?:\.\d+)?)\s*(?:Mu|Mtr|Meter)\s*([\d,]+(?:\.\d+)?)',
                'name_extraction': 'before_first_number'
            },
            'sujan_impex': {
                'indicators': ['Sujan Impex', 'SUJAN IMPEX', 'Fabrics & More'],
                'item_pattern': r'(\d+(?:\.\d+)?)\s*(?:Mtr|Meter|Pcs|Piece)\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*(?:Mtr|Meter)\s*([\d,]+(?:\.\d+)?)',
                'name_extraction': 'structured_table'
            },
            'home_ideas': {
                'indicators': ['Home Ideas', 'HOME IDEAS', 'DDECOR'],
                'item_pattern': r'(\d+(?:\.\d+)?)\s*(?:Mtr|Meter|Pcs|Piece)\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*(?:Mtr|Meter)\s*([\d,]+(?:\.\d+)?)',
                'name_extraction': 'generic'
            }
        }
    
    def detect_format(self, text: str) -> str:
        """Automatically detect invoice format based on content"""
        text_lower = text.lower()
        
        for format_name, format_info in self.format_patterns.items():
            for indicator in format_info['indicators']:
                if indicator.lower() in text_lower:
                    print(f"🔍 Detected {format_name.upper()} format")
                    return format_name
        
        print("🔍 Format not detected, using generic parser")
        return 'generic'
    
    def parse_invoice(self, text: str) -> List[InvoiceLine]:
        """Parse invoice using the detected format"""
        format_type = self.detect_format(text)
        
        if format_type == 'sarom':
            return self._parse_sarom_format(text)
        elif format_type == 'sujan_impex':
            return self._parse_sujan_impex_format(text)
        elif format_type == 'home_ideas':
            return self._parse_home_ideas_format(text)
        else:
            return self._parse_generic_format(text)
    
    def _parse_sarom_format(self, text: str) -> List[InvoiceLine]:
        """Parse Sarom format: '4.15 Mtr 720.00 Mtr 2,988.00'"""
        print("📋 Parsing SAROM format...")
        fabric_details = []
        
        # Multiple patterns for Sarom format variations
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:My|Mtr|Meter|Mtr,|Mtr~|Mtr\")\s*(\d+(?:\.\d+)?)\s*(?:Mu|Mtr|Meter)\s*([\d,]+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:Mtr|Meter)\s*(\d+(?:\.\d+)?)\s*(?:Mtr|Meter)\s*([\d,]+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)(?:Mtr|Meter)(?:,|~|-)\s*(\d+(?:\.\d+)?)\s*(?:Mtr|Meter)\s*([\d,]+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*Mtr~\s*,?\s*(\d+(?:\.\d+)?)\s*Mtr\s*([\d,]+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*Mtr,\s*(\d+(?:\.\d+)?)\s*Mtr\s*([\d,]+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*Mtr\"\s*(\d+(?:\.\d+)?)\s*Mtr\s*([\d,]+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*Mtr\s*(\d+(?:\.\d+)?)\s*Mtr\s*([\d,]+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:Mtr|Meter)\s*(\d+(?:\.\d+)?)\s*(?:Mtr|Meter)\s*([\d,]+(?:\.\d+)?)",
            # Additional patterns for OCR variations
            r"(\d+(?:\.\d+)?)\s*Mtr\"\s*(\d+(?:\.\d+)?)\s*Mtr\s*([\d,]+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*Mtr-\s*(\d+(?:\.\d+)?)\s*Mu\s*([\d,]+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*Mtr\s*(\d+(?:\.\d+)?)\s*Mtr\s*([\d,]+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*Mtr\s*(\d+(?:\.\d+)?)\s*Mtr\s*([\d,]+(?:\.\d+)?)",
            # Pattern for incomplete amounts (missing last digit)
            r"(\d+(?:\.\d+)?)\s*Mtr\"\s*(\d+(?:\.\d+)?)\s*Mtr\s*([\d,]+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*Mtr\s*(\d+(?:\.\d+)?)\s*Mtr\s*([\d,]+(?:\.\d+)?)",
            # More flexible amount pattern for incomplete amounts
            r"(\d+(?:\.\d+)?)\s*Mtr\"\s*(\d+(?:\.\d+)?)\s*Mtr\s*([\d,]+(?:\.\d+)?)",
            # Very flexible pattern for problematic lines like CASSIA - 115
            r"(\d+(?:\.\d+)?)\s*Mtr[^\d]*\s*(\d+(?:\.\d+)?)\s*Mtr\s*([\d,]+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*Mtr[^\d]*\s*(\d+(?:\.\d+)?)\s*Mtr\s*([\d,]+(?:\.\d+)?)",
        ]
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Try all patterns
            for pattern in patterns:
                match = re.search(pattern, line, re.I)
                if match:
                    qty = float(match.group(1))
                    rate = float(match.group(2))
                    amount = float(match.group(3).replace(',', ''))
                    
                    # Extract material name - everything before the first number
                    name_part = line[:match.start()].strip()
                    if name_part:
                        # Clean the name more aggressively for Sarom format
                        clean_name = self._clean_sarom_fabric_name(name_part)
                        if clean_name and len(clean_name) >= 3:
                            print(f"   ✅ {clean_name} | Qty: {qty} | Rate: {rate} | Amount: {amount}")
                            fabric_details.append(InvoiceLine(material_name=clean_name, quantity=qty, amount=amount, rate=rate))
                            break
        
        print(f"📊 SAROM format: Found {len(fabric_details)} fabric items")
        return fabric_details
    
    def _clean_sarom_fabric_name(self, name: str) -> str:
        """Special cleaning for Sarom format to remove OCR artifacts"""
        if not name:
            return ""
        
        # Remove common Sarom-specific noise patterns
        noise_patterns = [
            r'\b5%\b',  # Tax percentage
            r'\b\d{8}\b',  # HSN codes like 55169200
            r'\b\d{6,7}\b',  # Other numeric codes (6-7 digits)
            r'\b\d{1,2}\b',  # Single/double digit numbers
            r'[A-Z]{2}\d{2}[A-Z]{5}\d[A-Z]\d[A-Z]\d',  # GSTIN-like patterns
            r'\b[A-Za-z]{8,}\d{2,}\b',  # Long alphanumeric codes like "Isstegz00"
            r'\b\d{2,}[A-Za-z]{3,}\d{2,}\b',  # Mixed alphanumeric codes
            r'\b[A-Za-z]{4,}\d{2,}[A-Za-z]{2,}\d{2,}\b',  # Complex alphanumeric like "Isstegz00"
            r'\b[A-Za-z]{6,}\d{2,}\b',  # Long text followed by numbers like "Isstegz00"
            r'[^\w\s\-]',  # Remove all punctuation except hyphens
            r'\s+',  # Multiple spaces
            r'^\s+|\s+$',  # Leading/trailing spaces
        ]
        
        for pattern in noise_patterns:
            name = re.sub(pattern, " ", name, flags=re.I)
        
        # Clean up extra whitespace and normalize
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove leading/trailing hyphens and clean up
        name = re.sub(r'^[-]+|[-]+$', '', name)
        name = name.strip()
        
        # Return if meaningful
        if len(name) >= 3 and not re.fullmatch(r'[\d\s]+', name):
            return name
        
        return ""
    
    def _parse_sujan_impex_format(self, text: str) -> List[InvoiceLine]:
        """Parse Sujan Impex format using working regex pattern for HSN/Qty/Rate/Amount"""
        print("📋 Parsing SUJAN IMPEX format...")
        fabric_details = []
        
        # Use the working regex pattern for Sujan Impex layout
        ITEM_LINE_RE = re.compile(
            r"""(?m)^
                (?P<desc>.+?)                         # description until HSN
                \s+(?P<hsn>\d{8})\s+                  # 8-digit HSN
                (?P<qty>\d+(?:\.\d+)?)\s*(?:MTR|Mtr|Meter|Meters|Mtrs)\s+
                (?P<rate>[\d,]+(?:\.\d{2})?)\s*(?:MTR|Mtr|Meter|Meters|Mtrs)\s+
                (?P<amount>[\d,]+(?:\.\d{2})?)
                \s*$
            """,
            re.IGNORECASE | re.VERBOSE
        )
        
        for match in ITEM_LINE_RE.finditer(text):
            desc_raw = re.sub(r"\s+", " ", match.group("desc")).strip()
            qty = float(match.group("qty"))
            rate = float(match.group("rate").replace(",", ""))
            amount = float(match.group("amount").replace(",", ""))
            
            print(f"   🔍 Found item: {desc_raw}")
            print(f"      📏 HSN: {match.group('hsn')}, Qty: {qty}, Rate: {rate}, Amount: {amount}")
            
            # Clean the fabric name
            clean_name = self._clean_fabric_name(desc_raw)
            if clean_name and len(clean_name) >= 3:
                print(f"   ✅ {clean_name} | Qty: {qty} | Rate: {rate} | Amount: {amount}")
                fabric_details.append(InvoiceLine(
                    material_name=clean_name,
                    quantity=qty,
                    amount=amount,
                    rate=rate
                ))
            else:
                print(f"   ⚠️ Skipping {desc_raw} - name too short after cleaning")
        
        print(f"📊 SUJAN IMPEX format: Found {len(fabric_details)} fabric items")
        return fabric_details
    
    def _parse_home_ideas_format(self, text: str) -> List[InvoiceLine]:
        """Parse Home Ideas format using working table structure approach"""
        print("📋 Parsing HOME IDEAS format...")
        fabric_details = []
        
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        
        # Look for line items that start with a 10-digit Order No
        starts_line_item = re.compile(r"^\d{10}\s")
        
        for line in lines:
            if starts_line_item.match(line):
                print(f"   🔍 Found line item: {line}")
                
                # Tokenize the line and parse from the right side
                tokens = line.split()
                
                # Expect at least: [order_no] [collection words ...] [sr_no] [rl/cl] [dc_no] [lr] [meters] [rate] [basic] [taxable]
                if len(tokens) >= 11:
                    order_no = tokens[0]
                    basic = tokens[-2]      # Basic Price
                    taxable = tokens[-1]    # Taxable Value  
                    rate = tokens[-3]       # Rate per meter
                    meters = tokens[-4]     # Meters/Quantity
                    lr = tokens[-5]         # LR Details
                    dc_no = tokens[-6]      # DC No
                    rlcl = tokens[-7]       # RL/CL
                    sr_no = tokens[-8]      # Sr No
                    collection = " ".join(tokens[1:-8])  # Everything between order_no and sr_no
                    
                    print(f"      📋 Order: {order_no}, Collection: {collection}")
                    print(f"      📏 Meters: {meters}, Rate: {rate}, Basic: {basic}")
                    
                    try:
                        # Convert to proper types
                        qty = float(meters)
                        rate_val = float(rate.replace(',', ''))
                        amount = float(basic.replace(',', ''))
                        
                        # Validate the data
                        if qty > 0 and rate_val > 0 and amount > 0:
                            # Clean the collection name
                            clean_name = self._clean_fabric_name(collection)
                            if clean_name and len(clean_name) >= 3:
                                print(f"   ✅ {clean_name} | Qty: {qty} | Rate: {rate_val} | Amount: {amount}")
                                fabric_details.append(InvoiceLine(
                                    material_name=clean_name, 
                                    quantity=qty, 
                                    amount=amount, 
                                    rate=rate_val
                                ))
                            else:
                                print(f"   ⚠️ Skipping {collection} - name too short after cleaning")
                        else:
                            print(f"   ⚠️ Invalid values: qty={qty}, rate={rate_val}, amount={amount}")
                            
                    except ValueError as e:
                        print(f"   ❌ Error parsing values: {e}")
                        continue
                else:
                    print(f"   ⚠️ Line too short, expected 11+ tokens, got {len(tokens)}")
                    continue
        
        print(f"📊 HOME IDEAS format: Found {len(fabric_details)} fabric items")
        return fabric_details
    
    def _parse_generic_format(self, text: str) -> List[InvoiceLine]:
        """Generic parser for unknown formats"""
        print("📋 Using generic parser...")
        fabric_details = []
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Look for any line with numbers and text that might be fabric
            if re.search(r'[A-Za-z]', line) and re.search(r'\d+', line):
                name, qty, rate, amount = self._extract_fabric_from_line(line, lines, i)
                
                if name and qty and rate and amount:
                    clean_name = self._clean_fabric_name(name)
                    if clean_name:
                        print(f"   ✅ {clean_name} | Qty: {qty} | Rate: {rate} | Amount: {amount}")
                        fabric_details.append(InvoiceLine(material_name=clean_name, quantity=qty, amount=amount, rate=rate))
        
        print(f"📊 Generic parser: Found {len(fabric_details)} fabric items")
        return fabric_details
    
    def _find_rate_amount_in_context(self, lines: List[str], current_line: int) -> Tuple[Optional[float], Optional[float]]:
        """Find rate and amount in context around the current line"""
        rate = None
        amount = None
        
        # Look in current line and nearby lines
        for i in range(max(0, current_line - 2), min(len(lines), current_line + 3)):
            line = lines[i].strip()
            
            # Look for rate patterns
            if not rate:
                rate_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:per|/)\s*(?:mtr|meter|pcs)', line, re.I)
                if rate_match and rate_match.group(1):
                    try:
                        rate = float(rate_match.group(1))
                    except ValueError:
                        pass
            
            # Look for amount patterns
            if not amount:
                amt_match = re.search(r'₹?\s*([\d,]+(?:\.\d+)?)', line)
                if amt_match and amt_match.group(1):
                    try:
                        amount = float(amt_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
        
        return rate, amount
    
    def _extract_fabric_from_line(self, line: str, lines: List[str], line_index: int) -> Tuple[Optional[str], Optional[float], Optional[float], Optional[float]]:
        """Extract fabric information from a line"""
        # This is a simplified extractor - can be enhanced based on specific needs
        name = None
        qty = None
        rate = None
        amount = None
        
        # Extract name (text before first number)
        name_match = re.match(r'^([A-Za-z\s\-]+)', line)
        if name_match:
            name = name_match.group(1).strip()
        
        # Extract quantity
        qty_match = re.search(r'(\d+(?:\.\d+)?)', line)
        if qty_match:
            qty = float(qty_match.group(1))
        
        # Look for rate and amount in context
        rate, amount = self._find_rate_amount_in_context(lines, line_index)
        
        return name, qty, rate, amount
    
    def _clean_fabric_name(self, name: str) -> str:
        """Clean fabric name by removing noise while preserving important details"""
        if not name:
            return ""
        
        # Remove common invoice noise but be more conservative
        noise_patterns = [
            r'\b(GSTIN|GST|IGST|CGST|SGST|Tax|Total|Sub[- ]?total|Grand Total|Invoice|Bill|Address|Ship To|PIN|Pincode|Phone|Mobile|Email)\b',
            r'[A-Z]{2}\d{2}[A-Z]{5}\d[A-Z]\d[A-Z]\d',  # GSTIN-like
            r'\b\d{6}\b',
            r'\b5%\b',  # Tax percentages
            r'\|\s*%[^|]*$',  # Trailing tax info
            r'^\d+\s+',  # Leading line numbers
            r'\s+\$\d+\s*',  # Dollar amounts
            r'\s+§\d+\s*',  # Section symbols
        ]
        
        for pattern in noise_patterns:
            name = re.sub(pattern, "", name, flags=re.I)
        
        # Clean up extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'^[:\-\s|]+|[:\-\s|]+$', '', name)
        
        # Return if meaningful
        if len(name) >= 3 and not re.fullmatch(r'[₹\d\s\.,/-]+', name):
            return name
        
        return ""

# ========== Compare ==========
@dataclass
class MatchRow:
    invoice_name: str
    quantity: Optional[float]
    rate: Optional[float]              # computed amount/qty
    db_name: Optional[str]
    db_rate: Optional[float]
    score: float
    status: str  # "✅ MATCH" | "❌ MISMATCH" | "ℹ️ NOT FOUND"

def compare(inv_lines: List[InvoiceLine], db_items: List[DBItem]) -> List[MatchRow]:
    tol = float(os.getenv("RATE_TOLERANCE_PCT", "0.10"))
    db_index = build_db_index(db_items)
    rows: List[MatchRow] = []

    for il in inv_lines:
        db_it, sc = best_match(il.material_name, db_index)
        if not db_it:
            rows.append(MatchRow(il.material_name, il.quantity, il.rate, None, None, sc, "ℹ️ NOT FOUND"))
            continue

        inv_rate = il.rate
        db_rate = db_it.default_purchase_price
        if inv_rate is None or db_rate is None:
            rows.append(MatchRow(il.material_name, il.quantity, inv_rate, db_it.material_name, db_rate, sc, "❌ MISMATCH"))
            continue

        ok = abs(inv_rate - db_rate) <= (db_rate * tol)
        rows.append(MatchRow(
            invoice_name=il.material_name,
            quantity=il.quantity,
            rate=inv_rate,
            db_name=db_it.material_name,
            db_rate=db_rate,
            score=round(sc, 2),
            status="✅ MATCH" if ok else "❌ MISMATCH",
        ))
    return rows

# ========== Enhanced Main Function ==========
def main():
    if len(sys.argv) < 2:
        print("Usage: python test_basic_ocr.py /path/to/invoice.(pdf|png|jpg|...)")
        sys.exit(2)

    _wire_tesseract()

    invoice_path = sys.argv[1]
    if not Path(invoice_path).exists():
        print(f"File not found: {invoice_path}")
        sys.exit(1)

    print("→ Extracting text…")
    text = extract_text(invoice_path)
    if not text:
        print("No text extracted."); sys.exit(1)

    # If this is a Home Ideas / D'Decor invoice, pull totals
    totals = extract_homeideas_totals(text)
    # if any([totals.sub_total, totals.courier_charges, totals.add_charges, totals.taxable_value, 
    #         totals.tcs_amount, totals.igst_amount, totals.cgst_amount, totals.sgst_amount, totals.total_inc_taxes]):
    #     print("\n🧾 HOME IDEAS / D'DECOR — TOTALS")
    #     print(f"   Sub Total         : {_fmt_money(totals.sub_total)}")
    #     print(f"   Courier Charges   : {_fmt_money(totals.courier_charges)}")
    #     print(f"   Add/Charges       : {_fmt_money(totals.add_charges)}")
    #     print(f"   Taxable Value     : {_fmt_money(totals.taxable_value)}")
    #     print(f"   TCS Amount        : {_fmt_money(totals.tcs_amount)}")
    #     print(f"   IGST Amount       : {_fmt_money(totals.igst_amount)}")
    #     print(f"   CGST Amount       : {_fmt_money(totals.cgst_amount)}")
    #     print(f"   SGST Amount       : {_fmt_money(totals.sgst_amount)}")
    #     print(f"   TOTAL INC. TAXES  : {_fmt_money(totals.total_inc_taxes)}")

    # → Extract IGST
    igst_lines = extract_igst_lines(text)
    best_igst  = pick_invoice_igst(igst_lines)

    # if igst_lines:
    #     print("\n🧾 IGST DETECTED:")
    #     for t in igst_lines:
    #         rp = f"{t.rate_pct:.2f}%" if t.rate_pct is not None else "—"
    #         am = f"₹{t.amount:.2f}"    if t.amount is not None    else "—"
    #         print(f"   • Line: {t.line_text}")
    #         print(f"     Rate: {rp} | Amount: {am}")
    #     if best_igst:
    #         rp = f"{best_igst.rate_pct:.2f}%" if best_igst.rate_pct is not None else "—"
    #         am = f"₹{best_igst.amount:.2f}"    if best_igst.amount is not None    else "—"
    #         print(f"   ⇒ Picked as invoice IGST: Rate {rp}, Amount {am}")

    # Sujan Impex: Output IGST-<city>
    out_igst = extract_output_igst_total(text)
    # if out_igst:
    #     print("\n🧾 OUTPUT IGST (Sujan Impex):")
    #     amt = f"₹{out_igst.amount:.2f}" if out_igst.amount is not None else "—"
    #     print(f"   Label: {out_igst.label}")
    #     print(f"   Amount: {amt}")

    # → Sarom totals: CGST / SGST (only for non-Sujan Impex invoices)
    taxes = extract_cgst_sgst_roundoff(text)
    
    # Check if this is a Sujan Impex invoice
    is_sujan_impex = 'sujan impex' in text.lower() or out_igst is not None
    
    if not is_sujan_impex:
        # Check if "SALES" is mentioned in the invoice to adjust labels
        has_sales = 'sales' in text.lower()
        cgst_label = "CGST SALES" if has_sales else "CGST"
        sgst_label = "SGST SALES" if has_sales else "SGST"
        
        # print("\n🧾 TAX (Sarom):")
        # print(f"   GST Rate   : {('%.1f%%' % taxes.gst_rate) if taxes.gst_rate is not None else '—'}")
        # print(f"   {cgst_label:<12}: {('₹%.2f' % taxes.cgst) if taxes.cgst is not None else '—'}")
        # print(f"   {sgst_label:<12}: {('₹%.2f' % taxes.sgst) if taxes.sgst is not None else '—'}")

    print("→ Parsing with Universal Multi-Format Parser…")
    
    # Use the new universal parser
    parser = UniversalInvoiceParser()
    inv = parser.parse_invoice(text)
    
    if not inv:
        print("No valid fabric items found."); sys.exit(1)

    print("→ Loading CSV Fabric Database…")
    csv_fabrics = load_csv_fabrics()
    
    print("→ Loading DB (material_name, default_purchase_price)…")
    db = load_db_items()
    if not db:
        print("⚠️ No DB rows loaded. Continuing with CSV matching only...")
        db = []

    print("\n🔍 CSV FABRIC MATCHING RESULTS:")
    print("=" * 120)
    print(f"{'Invoice Name':<40} {'Qty':>8} {'Rate':>12} {'Amount':>12} {'CSV Match':<50} {'CSV Price':>12} {'Method':<25} {'Score':>6}")
    print("-" * 120)
    
    total_invoice_value = 0
    total_csv_value = 0
    matched_items = 0
    
    for line in inv:
        # Find CSV match
        csv_match = find_csv_fabric_match(line.material_name, csv_fabrics)
        
        # Calculate amounts
        amount = line.amount if line.amount else (line.rate * line.quantity if line.rate and line.quantity else 0)
        total_invoice_value += amount
        
        if csv_match:
            matched_items += 1
            csv_price = float(csv_match['fabric']['default_price']) if csv_match['fabric']['default_price'] else 0
            csv_amount = csv_price * line.quantity if line.quantity else 0
            total_csv_value += csv_amount
            
            # Calculate price difference
            if line.rate and csv_price:
                price_diff = abs(line.rate - csv_price)
                price_diff_pct = (price_diff / csv_price) * 100
                
                # More granular price difference categories with clearer mismatch indicators
                if price_diff_pct == 0:
                    status = "✅ MATCHED WITH DATABASE (Price: ✅ EXACT MATCH)"
                    price_match_status = "✅ PRICE MATCHES"
                elif price_diff_pct <= 2:
                    status = "✅ MATCHED WITH DATABASE (Price: ✅ MINOR DIFFERENCE)"
                    price_match_status = "⚠️ PRICE MINOR DIFFERENCE"
                elif price_diff_pct <= 5:
                    status = "⚠️ MATCHED WITH DATABASE (Price: ❌ SMALL DIFFERENCE)"
                    price_match_status = "❌ PRICE DOESN'T MATCH (Small)"
                elif price_diff_pct <= 10:
                    status = "⚠️ MATCHED WITH DATABASE (Price: ❌ MODERATE DIFFERENCE)"
                    price_match_status = "❌ PRICE DOESN'T MATCH (Moderate)"
                elif price_diff_pct <= 25:
                    status = "❌ MATCHED WITH DATABASE (Price: ❌ SIGNIFICANT DIFFERENCE)"
                    price_match_status = "❌ PRICE DOESN'T MATCH (Significant)"
                else:
                    status = "❌ MATCHED WITH DATABASE (Price: ❌ MAJOR DIFFERENCE)"
                    price_match_status = "❌ PRICE DOESN'T MATCH (Major)"
            else:
                status = "✅ MATCHED WITH DATABASE"
                price_match_status = "✅ PRICE MATCHES"
            
            print(f"{line.material_name[:40]:<40} {line.quantity:>8.2f} {line.rate:>12.2f} {amount:>12.2f} "
                  f"{csv_match['csv_name_no_prefix'][:50]:<50} {csv_price:>12.2f} "
                  f"{csv_match['method'][:25]:<25} {csv_match['score']:>6.1f}")
            
            # Show enhanced match details
            print(f"   📊 Match Details:")
            print(f"      Database Name: {csv_match['csv_name_no_prefix']}")
            print(f"      Database Supplier: {csv_match['fabric'].get('supplier', 'Unknown')}")
            print(f"      Database Price: ₹{csv_price:.2f}")
            print(f"      Match Method: {csv_match['method']}")
            print(f"      Confidence Score: {csv_match['score']:.1f}%")
            
            # Show price analysis
            if line.rate and csv_price:
                print(f"      💰 Price Analysis:")
                print(f"         Invoice Rate: ₹{line.rate:.2f}")
                print(f"         Database Price: ₹{csv_price:.2f}")
                print(f"         Difference: ₹{price_diff:.2f} ({price_diff_pct:.1f}%)")
                print(f"         Status: {status}")
                
                # Add prominent price mismatch indicator
                if price_diff_pct > 0:
                    if price_diff_pct <= 2:
                        print(f"         🟡 PRICE STATUS: {price_match_status}")
                    else:
                        print(f"         🔴 PRICE STATUS: {price_match_status}")
                        print(f"         ⚠️  ATTENTION: Invoice price differs from database price!")
                else:
                    print(f"         🟢 PRICE STATUS: {price_match_status}")
        else:
            print(f"{line.material_name[:40]:<40} {line.quantity:>8.2f} {line.rate:>12.2f} {amount:>12.2f} "
                  f"{'❌ NO DATABASE MATCH':<50} {'—':>12} {'—':<25} {'—':6}")
            print(f"   🚨 Status: ❌ NOT MATCHED WITH DATABASE")
            print(f"      This fabric is not found in the database")
            print(f"      Consider adding it to the CSV database")
    
    print("-" * 120)
    
    # Enhanced summary with database match analysis
    print(f"📊 ENHANCED SUMMARY:")
    print(f"   Total Items: {len(inv)}")
    print(f"   ✅ Matched with Database: {matched_items}")
    print(f"   ❌ Not Matched with Database: {len(inv) - matched_items}")
    print(f"   Match Percentage: {matched_items/len(inv)*100:.1f}%")
    
    # Overall match status
    if matched_items == len(inv):
        match_status = "✅ EXCELLENT"
    elif matched_items >= len(inv) * 0.8:
        match_status = "⚠️ GOOD"
    elif matched_items >= len(inv) * 0.5:
        match_status = "❌ NEEDS ATTENTION"
    else:
        match_status = "❌ POOR"
    
    print(f"   Overall Status: {match_status}")
    
    print(f"\n💰 VALUE ANALYSIS:")
    print(f"   Total Invoice Value: ₹{total_invoice_value:.2f}")
    print(f"   Total Database Value: ₹{total_csv_value:.2f}")
    if total_csv_value > 0:
        value_diff = abs(total_invoice_value - total_csv_value)
        value_diff_pct = (value_diff / total_csv_value) * 100
        print(f"   Value Difference: ₹{value_diff:.2f} ({value_diff_pct:.1f}%)")
        
        # Price status
        if value_diff_pct <= 10:
            price_status = "✅ MATCHED"
        elif value_diff_pct <= 25:
            price_status = "⚠️ DIFFERENCE"
        else:
            price_status = "❌ HIGH DIFFERENCE"
        print(f"   Price Status: {price_status}")
    else:
        print(f"   Value Difference: ℹ️ NO COMPARISON (no database matches)")

    # Add price mismatch summary
    if total_csv_value > 0:
        print(f"\n🚨 PRICE MISMATCH SUMMARY:")
        price_mismatches = []
        minor_differences = []
        exact_matches = []
        
        for line in inv:
            csv_match = find_csv_fabric_match(line.material_name, csv_fabrics)
            if csv_match and line.rate:
                csv_price = float(csv_match['fabric']['default_price']) if csv_match['fabric']['default_price'] else 0
                if csv_price > 0:
                    price_diff = abs(line.rate - csv_price)
                    price_diff_pct = (price_diff / csv_price) * 100
                    
                    if price_diff_pct == 0:  # Exact match
                        exact_info = {
                            'fabric_name': line.material_name,
                            'invoice_rate': line.rate,
                            'database_price': csv_price
                        }
                        exact_matches.append(exact_info)
                    elif price_diff_pct > 2:  # More than 2% difference
                        mismatch_info = {
                            'fabric_name': line.material_name,
                            'invoice_rate': line.rate,
                            'database_price': csv_price,
                            'difference': price_diff,
                            'difference_pct': price_diff_pct,
                            'severity': 'HIGH' if price_diff_pct > 10 else 'MEDIUM' if price_diff_pct > 5 else 'LOW'
                        }
                        price_mismatches.append(mismatch_info)
                    elif price_diff_pct > 0:  # Minor differences (0-2%)
                        minor_info = {
                            'fabric_name': line.material_name,
                            'invoice_rate': line.rate,
                            'database_price': csv_price,
                            'difference': price_diff,
                            'difference_pct': price_diff_pct
                        }
                        minor_differences.append(minor_info)
        
        # Show exact matches first
        if exact_matches:
            print(f"   ✅ Items with EXACT Price Match:")
            for exact in exact_matches:
                print(f"      🟢 {exact['fabric_name'][:35]:<35} | "
                      f"Invoice: ₹{exact['invoice_rate']:>8.2f} | "
                      f"Database: ₹{exact['database_price']:>8.2f} | "
                      f"Status: ✅ PERFECT MATCH")
        
        # Show minor differences
        if minor_differences:
            print(f"\n   🟡 Items with Minor Price Differences (0-2%):")
            for minor in minor_differences:
                print(f"      🟡 {minor['fabric_name'][:35]:<35} | "
                      f"Invoice: ₹{minor['invoice_rate']:>8.2f} | "
                      f"Database: ₹{minor['database_price']:>8.2f} | "
                      f"Diff: ₹{minor['difference']:>6.2f} ({minor['difference_pct']:>5.1f}%) | "
                      f"Status: ⚠️ MINOR DIFFERENCE")
        
        # Show significant mismatches prominently
        if price_mismatches:
            print(f"\n   🔴 ITEMS WITH PRICE MISMATCHES (>2%):")
            print(f"   ⚠️  THESE PRICES DON'T MATCH THE DATABASE!")
            for mismatch in price_mismatches:
                severity_icon = "🔴" if mismatch['severity'] == 'HIGH' else "🟡" if mismatch['severity'] == 'MEDIUM' else "🟢"
                print(f"      {severity_icon} {mismatch['fabric_name'][:35]:<35} | "
                      f"Invoice: ₹{mismatch['invoice_rate']:>8.2f} | "
                      f"Database: ₹{mismatch['database_price']:>8.2f} | "
                      f"Diff: ₹{mismatch['difference']:>6.2f} ({mismatch['difference_pct']:>5.1f}%) | "
                      f"Status: ❌ PRICE DOESN'T MATCH | "
                      f"Severity: {mismatch['severity']}")
        else:
            print(f"\n   ✅ No significant price differences found (>2%)")
        
        # Summary of mismatches
        total_mismatches = len(price_mismatches) + len(minor_differences)
        if total_mismatches > 0:
            print(f"\n   📊 PRICE MATCH SUMMARY:")
            print(f"      Exact Matches: {len(exact_matches)}")
            print(f"      Minor Differences (0-2%): {len(minor_differences)}")
            print(f"      Significant Mismatches (>2%): {len(price_mismatches)}")
            print(f"      Total Items with Price Differences: {total_mismatches}")
            
            if len(price_mismatches) > 0:
                print(f"      ⚠️  ATTENTION: {len(price_mismatches)} items have significant price mismatches!")
                print(f"      🔍 Review these items for database updates or investigation!")

    print(f"\n   🧾 TAX SUMMARY:")
    if best_igst and best_igst.amount is not None:
        print(f"      IGST Amount: ₹{best_igst.amount:.2f}")
    if out_igst and out_igst.amount is not None:
        print(f"      Output IGST: ₹{out_igst.amount:.2f}")
    if taxes.gst_rate is not None:
        print(f"      GST Rate: {taxes.gst_rate:.1f}%")
    if taxes.cgst is not None:
        # Define labels here for tax summary
        has_sales = 'sales' in text.lower()
        cgst_label = "CGST SALES" if has_sales else "CGST"
        sgst_label = "SGST SALES" if has_sales else "SGST"
        print(f"      {cgst_label}: ₹{taxes.cgst:.2f}")
    if taxes.sgst is not None:
        # Define labels here for tax summary
        has_sales = 'sales' in text.lower()
        cgst_label = "CGST SALES" if has_sales else "CGST"
        sgst_label = "SGST SALES" if has_sales else "SGST"
        print(f"      {sgst_label}: ₹{taxes.sgst:.2f}")
        
        # Add Home Ideas / D'Decor totals to tax summary
        if totals.sub_total is not None:
            print(f"      Sub Total: ₹{totals.sub_total:.2f}")
        if totals.courier_charges is not None:
            print(f"      Courier Charges: ₹{totals.courier_charges:.2f}")
        if totals.add_charges is not None:
            print(f"      Add/Charges: ₹{totals.add_charges:.2f}")
        if totals.taxable_value is not None:
            print(f"      Taxable Value: ₹{totals.taxable_value:.2f}")
        if totals.tcs_amount is not None:
            print(f"      TCS Amount: ₹{totals.tcs_amount:.2f}")
        if totals.igst_amount is not None:
            print(f"      IGST Amount: ₹{totals.igst_amount:.2f}")
        if totals.cgst_amount is not None:
            print(f"      CGST Amount: ₹{totals.cgst_amount:.2f}")
        if totals.sgst_amount is not None:
            print(f"      SGST Amount: ₹{totals.sgst_amount:.2f}")
        if totals.total_inc_taxes is not None:
            print(f"      TOTAL INC. TAXES: ₹{totals.total_inc_taxes:.2f}")
    
    if db:
        print(f"\n🔍 LEGACY DB COMPARISON RESULTS:")
        print("=" * 118)
        print(f"{'Invoice Name':<50} {'Qty':>8} {'Rate (amt/qty)':>16}   {'DB Name':<30} {'DB Rate':>12}  {'Score':>6}  Status")
        print("-" * 118)
        for r in compare(inv, db):
            qty = f"{r.quantity:.2f}" if r.quantity is not None else "—"
            rr  = f"{r.rate:.2f}" if r.rate is not None else "—"
            dbr = f"{r.db_rate:.2f}" if r.db_rate is not None else "—"
            print(f"{r.invoice_name[:50]:<50} {qty:>8} {rr:>16}   {(r.db_name or '—')[:30]:<30} {dbr:>12}  {r.score:>6.1f}  {r.status}")
        print("-" * 118)
    else:
        print(f"\n⚠️ Legacy DB comparison skipped (no DB items loaded)")

if __name__ == "__main__":
    main()
