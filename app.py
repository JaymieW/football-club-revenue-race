import io
import os
import tempfile

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib
matplotlib.use("Agg")

from flask import Flask, request, send_file
from datavisualizer import build_sample_data, create_race_animation

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    # Allows your portfolio page (e.g., on port 5500 or GitHub Pages) to call this local API
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.route("/api/race-gif", methods=["GET"])
def race_gif():
    fps = max(5, min(int(request.args.get("fps", 20)), 30))
    df = build_sample_data()

    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        create_race_animation(df, output_path=tmp_path, fps=fps)
        with open(tmp_path, "rb") as f:
            buf = io.BytesIO(f.read())
        buf.seek(0)
        return send_file(buf, mimetype="image/gif", download_name="club_revenue_race.gif")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)