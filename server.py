"""Minimal Flask server — serves the GUI and provides a REST API."""

import json
import os
import threading

from flask import Flask, jsonify, request, send_from_directory

from scrape import load_offers, save_offers, run_all_scrapers

app = Flask(__name__, static_folder="static")

# Global state for tracking background scrape
_scrape_lock = threading.Lock()
_scrape_running = False
_scrape_result = None


# ------------------------------------------------------------------
# Static file serving
# ------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


# ------------------------------------------------------------------
# API endpoints
# ------------------------------------------------------------------

@app.route("/api/offers")
def get_offers():
    """Return all offers, optionally filtered by source and/or status."""
    db = load_offers()
    offers = db.get("offers", [])

    # Query param filters
    source = request.args.get("source")
    status = request.args.get("status")
    search = request.args.get("search", "").lower()

    if source:
        offers = [o for o in offers if o.get("source") == source]

    if status:
        if status == "active":
            # Show everything except "not_interested"
            offers = [o for o in offers if o.get("status") != "not_interested"]
        else:
            offers = [o for o in offers if o.get("status") == status]

    if search:
        offers = [
            o for o in offers
            if search in o.get("title", "").lower()
            or search in o.get("company", "").lower()
            or search in o.get("description", "").lower()
        ]

    # Sort by date_found descending, then by status (new first)
    status_order = {"new": 0, "seen": 1, "applied": 2, "not_interested": 3}
    offers.sort(key=lambda o: (
        status_order.get(o.get("status", "seen"), 1),
        o.get("date_found", ""),
    ))
    # Reverse date sort (newest first within same status)
    offers.sort(key=lambda o: o.get("date_found", ""), reverse=True)
    offers.sort(key=lambda o: status_order.get(o.get("status", "seen"), 1))

    return jsonify({
        "offers": offers,
        "total": len(offers),
        "last_scrape": db.get("last_scrape"),
    })


@app.route("/api/offers/<offer_id>/status", methods=["POST"])
def update_status(offer_id):
    """Update the status of a single offer."""
    body = request.get_json(force=True)
    new_status = body.get("status")

    if new_status not in ("new", "seen", "applied", "not_interested"):
        return jsonify({"error": "Invalid status"}), 400

    db = load_offers()
    for offer in db["offers"]:
        if offer["id"] == offer_id:
            offer["status"] = new_status
            save_offers(db)
            return jsonify({"ok": True, "id": offer_id, "status": new_status})

    return jsonify({"error": "Offer not found"}), 404


@app.route("/api/refresh", methods=["POST"])
def refresh():
    """Trigger a full scrape in a background thread."""
    global _scrape_running, _scrape_result

    if _scrape_running:
        return jsonify({"error": "Scrape already in progress"}), 409

    def _run():
        global _scrape_running, _scrape_result
        try:
            _scrape_result = run_all_scrapers()
        except Exception as e:
            _scrape_result = {"error": str(e)}
        finally:
            _scrape_running = False

    _scrape_running = True
    _scrape_result = None
    t = threading.Thread(target=_run, daemon=True)
    t.start()

    return jsonify({"ok": True, "message": "Scraping started"})


@app.route("/api/status")
def scrape_status():
    """Check if a scrape is running and get the last result."""
    return jsonify({
        "running": _scrape_running,
        "result": _scrape_result,
    })


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    host = "127.0.0.1"
    port = 5000
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            host = cfg.get("server", {}).get("host", host)
            port = cfg.get("server", {}).get("port", port)

    print(f"Starting CIFRE PhD Tracker at http://{host}:{port}")
    app.run(host=host, port=port, debug=True)
