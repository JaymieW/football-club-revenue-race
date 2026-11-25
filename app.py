import os
from flask import Flask, jsonify, send_file

app = Flask(__name__)

# Resolve the path to club_revenue_race.gif in the same folder as app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GIF_PATH = os.path.join(BASE_DIR, "club_revenue_race.gif")


@app.after_request
def add_cors_headers(response):
    # Allow requests from GitHub Pages or local dev servers
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.route("/", methods=["GET"])
def home():
    # Quick lightweight response so root checks don't 404 or trigger heavy work
    return jsonify({"status": "ok", "service": "football-club-revenue-race"}), 200


@app.route("/api/race-gif", methods=["GET"])
def race_gif():
    # Return a clear error if club_revenue_race.gif wasn't deployed with app.py
    if not os.path.exists(GIF_PATH):
        return jsonify({"error": "club_revenue_race.gif not found on server"}), 404

    # Stream the pre-rendered GIF directly without using Matplotlib/Pillow on Render
    return send_file(
        GIF_PATH,
        mimetype="image/gif",
        download_name="club_revenue_race.gif",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)