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


@app.route("/api/search-batch", methods=["POST"])
def search_batch():
    data = request.get_json(silent=True) or {}
    
    raw_tickers = str(data.get("tickers", "")).strip()
    source = str(data.get("source", "")).strip()
    market = str(data.get("market", "")).strip().upper()
    
    if not raw_tickers:
        return jsonify({"error": "Nenhum ticker fornecido."}), 400
        
    if source not in SCRAPER_REGISTRY:
        return jsonify({"error": "Fonte inválida."}), 400
        
    if market not in SUPPORTED_MARKETS:
        return jsonify({"error": "Mercado inválido."}), 400
        
    tickers = normalize_tickers_from_text(raw_tickers)
    scraper = SCRAPER_REGISTRY[source]
    
    rows = []
    errors = []
    
    for i, ticker in enumerate(tickers):
        # Apply delay between requests (except the first)
        if i > 0:
            time.sleep(1.5) # Configurable delay 1-2s
            
        try:
            result = scraper.scrape_quote(ticker=ticker, market=market)
            flat_row = flatten_scrape_result(result)
            rows.append(flat_row)
        except Exception as exc:
            errors.append({
                "ticker": ticker,
                "error": str(exc)
            })
            
    columns = build_ordered_columns(rows)
    
    payload = {
        "source": source,
        "market": market,
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
        output_file = output_dir / f"batch_{source}_{market}_{timestamp_str}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except Exception as e:
        # Don't fail the request if persistence fails, but log it
        print(f"Error saving batch: {e}")
        
    return jsonify(payload)


@app.route("/api/export-sheets", methods=["POST"])
def export_sheets():
    # Reload .env to ensure we pick up any recent manual edits
    load_dotenv()
    
    data = request.get_json(silent=True) or {}
    webhook_url = os.getenv("G_SHEETS_WEBHOOK_URL")
    
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
        return jsonify({
            "error": "Erro ao exportar para Google Sheets.",
            "details": str(exc)
        }), 500


@app.route("/api/sync-firebase", methods=["POST"])
def sync_firebase():
    data = request.get_json(silent=True) or {}
    
    if not data or "rows" not in data:
        return jsonify({"error": "Nenhum dado para sincronizar."}), 400
        
    success = firebase_manager.save_batch(data)
    
    if success:
        return jsonify({"status": "success", "message": "Batch sincronizado com o Firebase."})
    else:
        return jsonify({
            "error": "Erro ao sincronizar com o Firebase.",
            "details": "Verifique se o caminho para o ficheiro de credenciais no .env está correto."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
