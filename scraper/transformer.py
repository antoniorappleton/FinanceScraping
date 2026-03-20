import re
from typing import Any, Dict, List, Set

def normalize_tickers_from_text(raw_text: str) -> List[str]:
    """
    Clean raw text from textarea:
    - Split by newlines, commas, or spaces
    - Remove extra spaces
    - Convert to uppercase
    - Remove duplicates (preserving order)
    """
    # Split by any separator: newline, comma, semicolon, space
    parts = re.split(r"[\n,;\s]+", raw_text)
    
    seen: Set[str] = set()
    normalized: List[str] = []
    
    for p in parts:
        clean = p.strip().upper()
        if clean and clean not in seen:
            normalized.append(clean)
            seen.add(clean)
            
    return normalized

def flatten_scrape_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a nested scraper result into a flat dictionary for table rows.
    """
    row = {
        "source": result.get("source"),
        "market": result.get("market"),
        "ticker_requested": result.get("ticker_requested"),
        "ticker_used": result.get("ticker_used"),
        "url": result.get("url"),
    }
    
    # Extract title fields
    title = result.get("title", {})
    if isinstance(title, dict):
        row["ticker"] = title.get("ticker")
        row["company"] = title.get("company")
    
    # Extract metrics
    metrics = result.get("metrics", {})
    if isinstance(metrics, dict):
        for k, v in metrics.items():
            # Don't overwrite existing top-level keys if they come from metrics
            if k not in row:
                row[k] = v
                
    # Ensure ticker is present (fallback)
    if not row.get("ticker"):
        row["ticker"] = row.get("ticker_used") or row.get("ticker_requested")
        
    return row

def clean_float(val: Any) -> float:
    """
    Convert strings like "$10.5B", "5.2%", "(2.3)", "1,200.50" to float numbers.
    Handles multipliers (B, M, T).
    """
    if val is None or val == "-" or val == "":
        return 0.0
    if isinstance(val, (float, int)):
        return float(val)
    
    if not isinstance(val, str):
        return 0.0

    # Basic cleanup
    cleaned = val.replace("$", "").replace(",", "").replace("(", "-").replace(")", "").strip()
    
    # Handle percentages
    is_pct = "%" in cleaned
    cleaned = cleaned.replace("%", "")

    if not cleaned or cleaned == "-":
        return 0.0

    multiplier = 1.0
    if cleaned.endswith("B"):
        multiplier = 1_000_000_000.0
        cleaned = cleaned[:-1]
    elif cleaned.endswith("M"):
        multiplier = 1_000_000.0
        cleaned = cleaned[:-1]
    elif cleaned.endswith("T"):
        multiplier = 1_000_000_000_000.0
        cleaned = cleaned[:-1]
    elif cleaned.endswith("K"):
        multiplier = 1_000.0
        cleaned = cleaned[:-1]

    try:
        num = float(cleaned) * multiplier
        if is_pct:
            return num / 100.0
        return num
    except ValueError:
        return val # Return original if it's not a simple number (e.g. a range "1.0 - 2.0")

def clean_row_for_firestore(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a row for Firestore:
    1. Cleans keys (no spaces, replace special chars).
    2. Converts numeric strings to floats using clean_float.
    3. Keeps identifying fields like 'ticker', 'company', 'url', 'source', 'market' as strings.
    """
    clean_row = {}
    
    # Identify non-numeric fields
    info_fields = {"ticker", "company", "url", "source", "market", "ticker_used", "ticker_requested", "name", "nome", "source_used", "lastFullSync"}

    for k, v in row.items():
        # 1. Clean Key
        # replace spaces with _, remove dots, slashes, remove parentheses, ensure lowercase
        clean_key = k.lower().replace(" ", "_").replace("/", "_").replace(".", "").replace("(", "").replace(")", "").replace("%", "pct").replace("-", "_")
        
        # 2. Clean Value
        if clean_key.lower() in info_fields or k.lower() in info_fields:
            clean_row[clean_key] = v
        elif isinstance(v, str) and any(char.isdigit() for char in v):
            # If it contains digits, try to clean as float
            clean_row[clean_key] = clean_float(v)
        else:
            clean_row[clean_key] = v
            
    return clean_row

def build_ordered_columns(rows: List[Dict[str, Any]]) -> List[str]:
    """
    Generate a unique list of column names from rows, prioritizing specific ones.
    """
    priority = [
        "ticker", 
        "ticker_used", 
        "company", 
        "source", 
        "market", 
        "price", 
        "Change", # Finviz style
        "Price",  # Fallback
        "Volume", 
        "Market Cap",
        "url"
    ]
    
    all_keys: Set[str] = set()
    for row in rows:
        all_keys.update(row.keys())
    
    ordered: List[str] = []
    
    # Add priority keys if they exist in any row
    for pk in priority:
        # Check case-insensitively or exactly? Let's try to match what's in all_keys
        matches = [k for k in all_keys if k.lower() == pk.lower()]
        if matches:
            # Pick the best match (exact if possible, else first)
            best = pk if pk in matches else matches[0]
            if best not in ordered:
                ordered.append(best)
                
    # Add remaining keys alphabetically
    remaining = sorted([k for k in all_keys if k not in ordered])
    ordered.extend(remaining)
    
    return ordered
