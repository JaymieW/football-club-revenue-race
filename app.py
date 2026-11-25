import io
import os
import tempfile

#This is newer version - November 25 2026 at 1117 pm
# Force Matplotlib to use the non-interactive 'Agg' backend before importing pyplot/animation
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")

from flask import Flask, jsonify, request, send_file
from datavisualizer import build_sample_data, create_race_animation

app = Flask(__name__)

# Store generated GIFs in /tmp (persists during the container's lifetime without bloating RAM)
CACHE_DIR = os.path.join(tempfile.gettempdir(), "revenue_race_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


@app.after_request
def add_cors_headers(response):
    # Allow requests from GitHub Pages or local dev servers
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.route("/", methods=["GET"])
def home():
    # Quick lightweight response so root checks don't 404 or trigger heavy rendering
    return jsonify({"status": "ok", "service": "football-club-revenue-race"}), 200


@app.route("/api/race-gif", methods=["GET"])
def race_gif():
    raw_fps = request.args.get("fps", 12)
    try:
        fps = int(raw_fps)
    except (TypeError, ValueError):
        fps = 12

    # Clamp FPS to a safe range for free-tier rendering
    fps = max(5, min(fps, 20))
    cached_path = os.path.join(CACHE_DIR, f"club_revenue_race_fps_{fps}.gif")

    # Serve the cached GIF immediately if it has already been generated
    if os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
        return send_file(
            cached_path,
            mimetype="image/gif",
            download_name="club_revenue_race.gif",
        )

    # Otherwise build once into a temp file, then atomically move it into the cache
    df = build_sample_data()
    fd, tmp_path = tempfile.mkstemp(suffix=".gif", dir=CACHE_DIR)
    os.close(fd)

    try:
        create_race_animation(df, output_path=tmp_path, fps=fps)
        os.replace(tmp_path, cached_path)

        with open(cached_path, "rb") as f:
            buf = io.BytesIO(f.read())
        buf.seek(0)
        return send_file(
            buf,
            mimetype="image/gif",
            download_name="club_revenue_race.gif",
        )
    finally:
        # Clean up temporary file if something failed before os.replace
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)