import json
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from scraper.registry import SCRAPER_REGISTRY, SUPPORTED_MARKETS

app = Flask(__name__)


@app.route("/")
def index():
    return render_template(
        "index.html",
        sources=list(SCRAPER_REGISTRY.keys()),
        markets=SUPPORTED_MARKETS,
    )


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

    try:
        result = scraper.scrape_quote(ticker=ticker, market=market)

        output_dir = Path("data/raw")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"{source}_{market}_{ticker}_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=2, ensure_ascii=False)

        return jsonify(result)

    except NotImplementedError as exc:
        return jsonify(
            {
                "error": "Fonte ainda não implementada.",
                "details": str(exc),
            }
        ), 501
    except Exception as exc:
        return jsonify(
            {
                "error": "Erro ao processar a pesquisa.",
                "details": str(exc),
            }
        ), 500


if __name__ == "__main__":
    app.run(debug=True)