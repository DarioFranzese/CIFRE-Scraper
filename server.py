"""Minimal Flask server — serves the GUI and provides a REST API."""

import json
import os
import threading
import webbrowser

from flask import Flask, jsonify, request, send_from_directory

from scrape import load_offers, save_offers, run_all_scrapers

app = Flask(__name__, static_folder="static")

# Global state for tracking background scrape
_scrape_lock = threading.Lock()
_scrape_running = False
_scrape_result = None


def start_background_scrape():
    """Start a full scrape in a background thread if not already running."""
    global _scrape_running, _scrape_result
    with _scrape_lock:
        if _scrape_running:
            return False
        _scrape_running = True
        _scrape_result = None

    def _run():
        global _scrape_running, _scrape_result
        try:
            _scrape_result = run_all_scrapers()
        except Exception as e:
            _scrape_result = {"error": str(e)}
        finally:
            with _scrape_lock:
                _scrape_running = False

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return True


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
    if not start_background_scrape():
        return jsonify({"error": "Scrape already in progress"}), 409

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
    open_browser = True
    refresh_on_start = True

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            srv_cfg = cfg.get("server", {})
            host = srv_cfg.get("host", host)
            port = srv_cfg.get("port", port)
            open_browser = srv_cfg.get("open_browser", open_browser)
            refresh_on_start = srv_cfg.get("refresh_on_start", refresh_on_start)

    url = f"http://{host}:{port}"
    print(f"Starting CIFRE PhD Tracker at {url}")

    # Werkzeug reloader in debug mode runs this file twice (supervisor & worker).
    # We only open the browser and trigger refresh in the main worker process.
    debug_mode = True
    is_main_worker = os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not debug_mode

    if is_main_worker:
        if refresh_on_start:
            print("Auto-refreshing offers in background...")
            threading.Timer(0.8, start_background_scrape).start()
        if open_browser:
            print(f"Opening browser at {url}...")
            threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    app.run(host=host, port=port, debug=debug_mode)
