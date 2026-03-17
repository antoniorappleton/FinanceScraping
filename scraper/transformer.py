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
