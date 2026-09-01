# backend/app.py
# ========================================================
# TTD FLASK API SERVER
# Connects: scraper.py + engine.py → Android/Dashboard
#
# ENDPOINTS:
# /api/health       → Is server alive?
# /api/live         → Main screen (new devotee data)
# /api/journey      → In-queue devotee (with location)
# /api/compartments → All 31 compartments detail
# /api/outdoor      → Outdoor queue segments
# /api/forecast     → Best time + hourly predictions
# ========================================================

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import time

from scraper import TTDLiveScraper
from engine import TTDCrowdEngine
# ========================================================
# HTML PAGES - Bulletproof file paths for cloud!
# ========================================================
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/dashboard')
def dashboard_page():
    return send_file(os.path.join(BASE_DIR, 'dashboard.html'))

@app.route('/places')
def places_page():
    return send_file(os.path.join(BASE_DIR, 'places.html'))

@app.route('/rooms')
def rooms_page():
    return send_file(os.path.join(BASE_DIR, 'rooms.html'))

@app.route('/phrases')
def phrases_page():
    return send_file(os.path.join(BASE_DIR, 'phrases.html'))

app = Flask(__name__)
CORS(app)  # Allows Android + Web to call this API

# ========================================================
# SMART CACHE SYSTEM
# Website updates every few hours, so we cache for 15 min
# This makes the API INSTANT + doesn't spam the website!
# ========================================================
cache = {
    "data": None,
    "result": None,
    "last_fetch": 0,
    "CACHE_MINUTES": 15
}

scraper = TTDLiveScraper()
engine  = TTDCrowdEngine()

def get_fresh_result(your_location=None):
    """
    Gets real data (uses cache if fetched recently).
    Cache = 15 minutes (website doesn't update faster anyway)
    """
    now = time.time()
    cache_age_minutes = (now - cache["last_fetch"]) / 60

    if cache["result"] is None or cache_age_minutes > cache["CACHE_MINUTES"]:
        print(f"\n🔄 Fetching FRESH data from website...")
        real_data      = scraper.get_live_data()
        cache["data"]  = real_data
        cache["last_fetch"] = now
        # Process WITHOUT location (base result)
        cache["result"] = engine.process(real_data)
    else:
        print(f"⚡ Using cached data ({cache_age_minutes:.1f} min old)")

    # If user gave location, re-process with it
    if your_location:
        return engine.process(cache["data"], your_location=your_location)

    return cache["result"]


# ========================================================
# ENDPOINT 1: HEALTH CHECK
# ========================================================
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status":  "online",
        "service": "TTD Pilgrim Smart System API",
        "version": "2.0",
        "time":    datetime.now().strftime('%d-%m-%Y %I:%M %p')
    })


# ========================================================
# ENDPOINT 2: LIVE MAIN SCREEN (NEW DEVOTEE)
# The money endpoint! Android home screen calls this!
# ========================================================
@app.route('/api/live', methods=['GET'])
def live():
    try:
        result = get_fresh_result()
        data   = result["scraped"]

        free  = data['wait_times'].get('free_darshan', {})
        ssd   = data['wait_times'].get('ssd_token', {})
        rs300 = data['wait_times'].get('rs300', {})

        return jsonify({
            "status":    "success",
            "timestamp": data["timestamp"],
            "source":    data["source"],

            # THE MAIN LOGIC: Where queue starts = where devotee joins
            "queue_starts_at": result["new_devotee"]["joins_at"],
            "wait_if_join_now": result["new_devotee"]["display"],

            # All ticket waits
            "wait_times": {
                "free_darshan": free.get('display', 'N/A'),
                "ssd_token":    ssd.get('display',  'N/A'),
                "rs300":        rs300.get('display','N/A'),
            },

            # Beginner guide for the location!
            "location_guide": result["new_devotee"]["guide"],

            # Journey route (forward only!)
            "journey_route": result["new_devotee"]["route"],

            # Live stats
            "crowd_status":       result["status"],
            "crowd_level":        data["crowd_level"],
            "pilgrims_waiting":   data["pilgrims_waiting"],
            "darshan_completed":  data["darshan_completed"],
            "active_compartments": data["active_compartments"],
            "total_compartments":  data["total_compartments"],
            "weather":            data["weather"],

            # Outdoor summary
            "outdoor": result["outdoor"],
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ========================================================
# ENDPOINT 3: MY JOURNEY (IN-QUEUE DEVOTEE)
# Android calls: /api/journey?location=vqc_middle
# ========================================================
@app.route('/api/journey', methods=['GET'])
def journey():
    try:
        your_location = request.args.get('location', None)

        if not your_location:
            # Return the list of valid positions to pick from
            result = get_fresh_result()
            tail   = result["scraped"]["queue_location"]
            valid  = engine.get_valid_positions(tail)

            return jsonify({
                "status": "success",
                "queue_tail": tail,
                "valid_positions": [
                    {"id": loc, "name": engine.DISPLAY_NAMES[loc]}
                    for loc, dist in valid
                ],
                "note": "Positions beyond today's tail are hidden (line doesn't reach there!)"
            })

        # Calculate their remaining wait
        result = get_fresh_result(your_location=your_location)

        return jsonify({
            "status":          "success",
            "your_position":   your_location,
            "position_name":   engine.DISPLAY_NAMES.get(your_location, your_location),
            "queue_tail":      result["scraped"]["queue_location"],
            "remaining_wait":  result["your_wait"]["display"],
            "route_forward":   result["your_wait"]["route"],
            "spot_guide":      result["your_wait"]["guide"],
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ========================================================
# ENDPOINT 4: ALL COMPARTMENTS (HEATMAP DATA!)
# ========================================================
@app.route('/api/compartments', methods=['GET'])
def compartments():
    try:
        result = get_fresh_result()

        return jsonify({
            "status":       "success",
            "active":       result["active_comp"],
            "total":        result["total_comp"],
            "compartments": result["compartments"],
            "heatmap_grid": result["vqc_grid"].tolist(),  # 3x11 grid for heatmap!
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ========================================================
# ENDPOINT 5: OUTDOOR QUEUE SEGMENTS
# ========================================================
@app.route('/api/outdoor', methods=['GET'])
def outdoor():
    try:
        result  = get_fresh_result()
        outdoor = result["outdoor"]

        return jsonify({
            "status":          "success",
            "total_in_system": outdoor["total_in_system"],
            "inside_vqc":      outdoor["inside_vqc"],
            "outside_line":    outdoor["outside_line"],
            "tail_location":   outdoor["tail_location"],
            "segments": {
                "krishnateja": {
                    "people": outdoor["krishnateja_fill"],
                    "status": "ACTIVE" if outdoor["krishnateja_fill"] > 0 else "EMPTY"
                },
                "octopus": {
                    "people": outdoor["octopus_fill"],
                    "status": "ACTIVE" if outdoor["octopus_fill"] > 0 else "EMPTY (beyond tail)"
                },
                "silathoranam": {
                    "people": outdoor["silathoranam_fill"],
                    "status": "🚨 EXTREME DAY - OPEN!" if outdoor["silathoranam_open"] else "CLOSED (opens on extreme days)"
                }
            }
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ========================================================
# ENDPOINT 6: FORECAST (Best time + hourly)
# ========================================================
@app.route('/api/forecast', methods=['GET'])
def forecast():
    try:
        result = get_fresh_result()
        bt     = result["best_time"]

        return jsonify({
            "status":     "success",
            "is_weekend": bt["is_weekend"],
            "best_time":  bt["best_time"],
            "hourly":     bt["hourly_predictions"],
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ========================================================
# RUN THE SERVER
# ========================================================
if __name__ == "__main__":
    print("="*55)
    print("🛕 TTD SMART SYSTEM - API SERVER STARTING")
    print("="*55)
    print("📡 Endpoints:")
    print("   http://localhost:5000/api/health")
    print("   http://localhost:5000/api/live       ← MAIN!")
    print("   http://localhost:5000/api/journey")
    print("   http://localhost:5000/api/compartments")
    print("   http://localhost:5000/api/outdoor")
    print("   http://localhost:5000/api/forecast")
    print("="*55)

    app.run(host="0.0.0.0", port=5000, debug=True)
