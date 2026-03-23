import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from scraper.registry import SCRAPER_REGISTRY, SUPPORTED_MARKETS
from scraper.transformer import (
    normalize_tickers_from_text,
    flatten_scrape_result,
    build_ordered_columns
)
from scraper.intelligent_router import scrape_multi_source
from scraper.firebase_manager import firebase_manager

# Load environment variables
load_dotenv()

app = Flask(__name__)


@app.route("/")
def index():
    return render_template(
        "index.html",
        sources=list(SCRAPER_REGISTRY.keys()),
        markets=SUPPORTED_MARKETS,
    )


@app.route("/api/search_ticker", methods=["POST"])
def search_ticker():
    data = request.get_json(silent=True) or {}

    query = str(data.get("query", "")).strip()
    market = str(data.get("market", "")).strip().upper()
    source = str(data.get("source", "")).strip()

    if not query:
        return jsonify({"error": "Query em falta."}), 400

    if market not in SUPPORTED_MARKETS:
        return jsonify({"error": "Mercado inválido."}), 400

    if source not in SCRAPER_REGISTRY:
        return jsonify({"error": "Fonte inválida."}), 400

    scraper = SCRAPER_REGISTRY[source]

    try:
        suggestions = scraper.search_ticker(query=query, market=market)
        return jsonify({
            "query": query,
            "market": market,
            "source": source,
            "suggestions": suggestions
        })
    except Exception as exc:
        return jsonify({
            "error": "Erro na pesquisa de ticker.",
            "details": str(exc),
            "suggestions": []
        }), 500


@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json(silent=True) or {}

    ticker = str(data.get("ticker", "")).strip().upper()
    source = str(data.get("source", "")).strip()
    market = str(data.get("market", "")).strip().upper()

    if not ticker:
        return jsonify({"error": "Ticker em falta."}), 400

    if not source or not market:
        result = scrape_multi_source(ticker)
        output_dir = Path("data/raw")
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        market_detected = result.get("detected_market", "unknown")
        asset_type = result.get("asset_type", "unknown")
        output_file = output_dir / f"auto_{asset_type}_{market_detected}_{ticker}_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        return jsonify(result)

    if source not in SCRAPER_REGISTRY:
        return jsonify({"error": "Fonte inválida."}), 400

    if market not in SUPPORTED_MARKETS:
        return jsonify({"error": "Mercado inválido."}), 400

    scraper = SCRAPER_REGISTRY[source]
    suggestions = []

    try:
        result = scraper.scrape_quote(ticker=ticker, market=market)

        output_dir = Path("data/raw")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"{source}_{market}_{ticker}_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=2, ensure_ascii=False)

        return jsonify(result)

    except NotImplementedError:
        error_msg = "Fonte ainda não implementada."
    except ValueError as ve:
        error_msg = str(ve)
        # Fallback to search_ticker for suggestions
        try:
            suggestions = scraper.search_ticker(query=ticker, market=market)
        except:
            suggestions = []
    except Exception as exc:
        error_msg = "Erro ao processar a pesquisa."
        suggestions = []

    return jsonify({
        "error": error_msg,
        "suggestions": suggestions,
        "try_tickers": [s.get("ticker") for s in suggestions[:3]]
    }), 500 if "NotImplementedError" not in error_msg else 501


@app.route("/api/analyze-etf", methods=["GET"])
def analyze_etf():
    ticker = request.args.get("ticker", "IU5C").upper().strip()
    if not ticker:
        return jsonify({"error": "Ticker required"}), 400
    
    try:
        # Scrape via intelligent multi-source (prioritizes justetf for ETFs)
        raw_data = scrape_multi_source(ticker)
        metrics = raw_data.get("metrics", {})
        
        # Enhanced Profit Max Algo per approved plan
        def safe_float(k, default=0.0):
            v = metrics.get(k, default)
            return float(v) if v is not None else default
        
        # Annualized returns
        ret_1y = safe_float("1_year")
        ret_3y = safe_float("3_years")
        ret_5y = safe_float("5_years")
        ann_3y = (1 + ret_3y) ** (1/3) - 1 if ret_3y > -1 else 0.0
        ann_5y = (1 + ret_5y) ** (1/5) - 1 if ret_5y > -1 else 0.0
        
        # Momentum & Risk
        mom_6m = safe_float("6_months")
        vol_1y = safe_float("volatility_1_year")
        dd_3y = safe_float("maximum_drawdown_3_years")
        rpr_3y = safe_float("return_per_risk_3_years")
        
        risk_score = 0.5 * vol_1y + 0.5 * abs(dd_3y)
        risk_level = "Low" if risk_score < 0.15 else "Medium" if risk_score < 0.25 else "High"
        
        # Weighted Score
        score = (0.25 * ann_3y + 0.25 * ann_5y + 
                 0.20 * rpr_3y + 0.15 * mom_6m + 
                 0.15 * (1 - vol_1y))
        score = max(0, min(1, score))  # Clamp 0-1
        
        # Signal w/ filters
        base_signal = "STRONG BUY" if score > 0.75 else "BUY" if score > 0.60 else "HOLD" if score > 0.45 else "AVOID"
        signal = base_signal
        trend = "Neutral"
        if mom_6m < 0:
            signal = "HOLD" if "BUY" in signal else signal  # Downgrade
            trend = "Downtrend" if safe_float("3_months") < 0 else "Weak Momentum"
        
        # Alloc suggestion (risk-adjusted, cap 20%)
        alloc_pct = int(score * (1 - risk_score) * 20)
        alloc_pct = min(alloc_pct, 20)
        
        # Div warnings
        sector_max = safe_float("telecommunication")  # Example top sector
        geo_us = safe_float("united_states")
        warnings = []
        if sector_max > 0.25:
            warnings.append("High sector concentration (>25%)")
        if geo_us > 0.30:
            warnings.append("High geo concentration (>30%)")
        
        # Top holdings for pie (all % keys ending digits)
        holdings = {k: v for k, v in metrics.items() if k.endswith(("_a", "_c")) or k in ["meta_platforms", "netflix", "comcast", "verizon_communications", "at&t", "walt_disney", "warner_bros_discovery", "t_mobile_us"] and isinstance(v, (int, float))}
        top_holdings = dict(sorted(holdings.items(), key=lambda x: x[1], reverse=True)[:8])
        
        analysis = {
            "ticker": ticker,
            "raw_metrics": metrics,
            "perf": {
                "1m": safe_float("1_month"),
                "3m": safe_float("3_months"),
                "6m": mom_6m,
                "1y": ret_1y,
                "ann_3y": ann_3y,
                "ann_5y": ann_5y,
            },
            "risk": {
                "vol_1y": vol_1y,
                "dd_3y": dd_3y,
                "risk_score": risk_score,
                "risk_level": risk_level
            },
            "algo": {
                "score": round(score, 3),
                "signal": signal,
                "trend": trend,
                "alloc_pct": f"{alloc_pct}%",
                "warnings": warnings
            },
            "holdings": top_holdings,
            "fund": {
                "ter": metrics.get("total_expense_ratio", "N/A"),
                "fund_size": metrics.get("fund_size", "N/A"),
                "replication": metrics.get("replication", "N/A")
            }
        }
        
        # Save analyzed data
        output_dir = Path("data/raw")
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"analyzed_etf_{ticker}_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/search-batch", methods=["POST"])
def search_batch():
    data = request.get_json(silent=True) or {}

    raw_tickers = str(data.get("tickers", "")).strip()
    source = str(data.get("source", "")).strip()
    market = str(data.get("market", "")).strip().upper()

    if not raw_tickers:
        return jsonify({"error": "Nenhum ticker fornecido."}), 400

    tickers = normalize_tickers_from_text(raw_tickers)
    rows = []
    errors = []

    # Always use intelligent routing (ignore source/market if provided, or use for all)
    for i, ticker in enumerate(tickers):
        # Rate limiting for batch
        if i > 0:
            time.sleep(1.5)
        try:
            result = scrape_multi_source(ticker)
            flat_row = flatten_scrape_result(result)
            rows.append(flat_row)
        except Exception as exc:
            errors.append({
                "ticker": ticker,
                "error": str(exc)
            })

    columns = build_ordered_columns(rows)
    payload = {
        "source": "intelligent_multi",  # Indicates auto-routing used
        "tickers_requested": tickers,
        "total_requested": len(tickers),
        "total_success": len(rows),
        "total_errors": len(errors),
        "columns": columns,
        "rows": rows,
        "errors": errors,
        "timestamp": datetime.now().isoformat()
    }
    # Persist batch result
    try:
        output_dir = Path("data/raw")
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"batch_intelligent_{timestamp_str}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"Batch saved to {output_file}")
    except Exception as e:
        print(f"Error saving batch: {e}")

    return jsonify(payload)


@app.route("/api/export-sheets", methods=["POST"])
def export_sheets():
    # Reload .env to ensure we pick up any recent manual edits
    load_dotenv(override=True)

    data = request.get_json(silent=True) or {}
    webhook_url = os.getenv("G_SHEETS_WEBHOOK_URL")
    print(f"DEBUG: Using webhook URL: {webhook_url[:40]}...")

    if not webhook_url or "COLE_O_URL" in webhook_url:
        return jsonify({"error": "URL da Google Sheet não configurado no .env"}), 400

    if not data or "rows" not in data:
        return jsonify({"error": "Nenhum dado para exportar."}), 400

    try:
        # Send data to Apps Script Webhook
        response = requests.post(webhook_url, json=data, timeout=30)
        response.raise_for_status()

        return jsonify(response.json())
    except Exception as exc:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error in export_sheets: {error_details}")
        return jsonify({
            "error": "Erro ao exportar para Google Sheets.",
            "details": str(exc),
            "traceback": error_details
        }), 500


@app.route("/portfolio", methods=["GET"])
def portfolio():
    ticker = request.args.get("ticker", "IU5C").upper()
    return render_template("portfolio.html", ticker=ticker)


@app.route("/api/load-recent")
def load_recent_batches():
    """Scan data/raw for recent batch JSON files and return structured data."""
    output_dir = Path("data/raw")
    if not output_dir.exists():
        return jsonify({"batches": []})
    
    cutoff_time = datetime.now().timestamp() - 24*60*60  # Last 24 hours
    
    batches = []
    for json_file in output_dir.glob("*.json"):
        if json_file.stat().st_mtime < cutoff_time:
            continue
            
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Check if it's a batch file with rows/columns
            if "rows" in data and "columns" in data and len(data["rows"]) > 0:
                preview_rows = data["rows"][:3]  # First 3 rows for preview
                
                batches.append({
                    "filename": json_file.name,
                    "path": str(json_file),
                    "timestamp": data.get("timestamp", json_file.stat().st_mtime),
                    "success": data.get("success", len(data["rows"])),
                    "total": data.get("total_requested", len(data["rows"])),
                    "rows": data["rows"],
                    "columns": data["columns"],
                    "preview": preview_rows
                })
        except (json.JSONDecodeError, KeyError):
            continue  # Skip invalid/malformed JSON files
    
    # Sort by timestamp desc (most recent first), limit 10
    batches.sort(key=lambda b: b["timestamp"], reverse=True)
    batches = batches[:10]
    
    return jsonify({
        "batches": batches,
        "count": len(batches)
    })


@app.route("/api/sync-firebase", methods=["POST"])
def sync_firebase():
    # Reload .env to pick up credentials path changes
    load_dotenv(override=True)
    data = request.get_json(silent=True) or {}

    if not data or "rows" not in data:
        return jsonify({"error": "Nenhum dado para sincronizar."}), 400

    # Check if Firebase is initialized
    if not firebase_manager.db:
        # Try to re-initialize in case .env was just fixed
        firebase_manager._initialize()
        if not firebase_manager.db:
            return jsonify({
                "error": "Firebase não inicializado.",
                "details": "Verifique se o ficheiro JSON de credenciais existe e se o caminho no .env está correto."
            }), 500

    # Use the new method that updates individual tickers in 'acoesDividendos'
    success = firebase_manager.save_batch_to_market_data(data)

    if success:
        return jsonify({"status": "success", "message": "Dados sincronizados com a coleção 'acoesDividendos'."})
    else:
        return jsonify({
            "error": "Erro ao sincronizar com o Firebase.",
            "details": "Ocorreu um erro ao atualizar os documentos. Verifique a consola do terminal para detalhes."
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)

