"""
Animated "bar chart race" of football club revenues.

What it does:
  1. Builds a small table of club revenues for 2017 and 2018 (in EUR millions).
  2. Fills in smooth in-between frames so bars grow/shrink instead of jumping.
  3. Draws each frame as a horizontal bar chart (club name on the left, revenue
     on the right, optional crest image, and a circular year indicator).
  4. Saves all frames as one animated GIF (or MP4 if the filename ends in .mp4).

Output: club_revenue_race.gif in the folder you run the script from.
"""

import os
# import numpy as np  # imported but not actually used anywhere in this script
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.offsetbox import OffsetImage, AnnotationBbox  # lets us place images on a plot
from matplotlib.patches import Arc  # used for the circular year/progress ring
from PIL import Image


def load_crest(path, zoom=0.22):
    # Load a club crest image safely; return None if missing.
    # If the file exists, open it, make sure it has a transparent background
    # (RGBA), and wrap it so matplotlib can place it on the chart.
    if path and os.path.exists(path):
        img = Image.open(path).convert("RGBA")
        return OffsetImage(img, zoom=zoom)
    # If the file is missing, the chart simply draws without that crest.
    return None


def build_sample_data():
    """Create sample multi-year revenue data (in € Millions)."""
    # Each row: (year, club, revenue in EUR millions, bar colour)
    rows = [
        # 2016
        (2016, "Real Madrid", 574.60, "#d62728"),
        (2016, "Barcelona", 548.30, "#1db954"),
        (2016, "Manchester United", 576.30, "#1f35c8"),
        (2016, "Bayern Munich", 487.80, "#7b2cbf"),
        (2016, "Manchester City", 427.70, "#d81b60"),
        (2016, "Paris Saint-Germain", 386.20, "#c5b31a"),
        (2016, "Arsenal", 387.60, "#2ecc40"),
        (2016, "Chelsea", 328.00, "#10b981"),
        (2016, "Liverpool", 324.20, "#17a2b8"),
        (2016, "Juventus", 305.70, "#4b0082"),
        (2016, "Tottenham Hotspur", 259.50, "#b85d19"),
        (2016, "Borussia Dortmund", 232.60, "#9acd32"),
        (2016, "Atlético Madrid", 172.50, "#2563eb"),
        (2016, "Inter Milan", 162.10, "#9333ea"),
        (2016, "Schalke 04", 130.20, "#a3b11a"),
        # 2017
        (2017, "Real Madrid", 674.60, "#d62728"),
        (2017, "Barcelona", 648.30, "#1db954"),
        (2017, "Manchester United", 676.30, "#1f35c8"),
        (2017, "Bayern Munich", 587.80, "#7b2cbf"),
        (2017, "Manchester City", 527.70, "#d81b60"),
        (2017, "Paris Saint-Germain", 486.20, "#c5b31a"),
        (2017, "Arsenal", 487.60, "#2ecc40"),
        (2017, "Chelsea", 428.00, "#10b981"),
        (2017, "Liverpool", 424.20, "#17a2b8"),
        (2017, "Juventus", 405.70, "#4b0082"),
        (2017, "Tottenham Hotspur", 359.50, "#b85d19"),
        (2017, "Borussia Dortmund", 332.60, "#9acd32"),
        (2017, "Atlético Madrid", 272.50, "#2563eb"),
        (2017, "Inter Milan", 262.10, "#9333ea"),
        (2017, "Schalke 04", 230.20, "#a3b11a"),
        # 2018
        (2018, "Barcelona", 818.10, "#1db954"),
        (2018, "Real Madrid", 745.63, "#d62728"),
        (2018, "Manchester United", 688.14, "#1f35c8"),
        (2018, "Bayern Munich", 655.47, "#7b2cbf"),
        (2018, "Paris Saint-Germain", 618.92, "#c5b31a"),
        (2018, "Manchester City", 599.66, "#d81b60"),
        (2018, "Liverpool", 596.48, "#17a2b8"),
        (2018, "Tottenham Hotspur", 507.66, "#b85d19"),
        (2018, "Chelsea", 505.37, "#10b981"),
        (2018, "Juventus", 448.86, "#4b0082"),
        (2018, "Arsenal", 435.01, "#2ecc40"),
        (2018, "Borussia Dortmund", 370.63, "#9acd32"),
        (2018, "Atlético Madrid", 361.22, "#2563eb"),
        (2018, "Inter Milan", 351.57, "#9333ea"),
        (2018, "Schalke 04", 306.62, "#a3b11a"),
    ]
    return pd.DataFrame(rows, columns=["year", "club", "revenue_m", "color"])

def interpolate_frames(df, steps_per_year=65, top_n=15):
    clean_df = (
        df.groupby(["year", "club"], as_index=False)["revenue_m"]
        .mean()
    )
    """Generate smooth intermediate frames between consecutive years."""
    years = sorted(clean_df["year"].unique())
    pivoted = (
        clean_df.pivot(index="year", columns="club", values="revenue_m")
        .reindex(years)
        .interpolate(method="linear")
    )
    # Reshape to one row per year, one column per club. Any gaps (a club missing
    # in some year) are filled by straight-line interpolation.
    pivoted = df.pivot(index="year", columns="club", values="revenue_m").reindex(years).interpolate(method="linear")

    # Lookup tables: club -> colour, club -> crest file path.
    colors = df.drop_duplicates("club").set_index("club")["color"].to_dict()
    # crests = df.drop_duplicates("club").set_index("club")["crest_path"].to_dict() #Removed the club logos

    frames = []
    # Loop over each pair of consecutive years (here just 2016 -> 2018).
    for idx in range(len(years) - 1):
        y0, y1 = years[idx], years[idx + 1]
        v0 = pivoted.loc[y0].fillna(0.0)
        v1 = pivoted.loc[y1].fillna(0.0)

        # Create `steps_per_year` frames between the 3 years.
        for step in range(steps_per_year):
            alpha = step / steps_per_year  # 0.0 at the start, approaching 1.0
            vals = v0 * (1 - alpha) + v1 * alpha  # blend the two years' values

            # Year shown in the ring; switches from 2017 to 2018 halfway through.
            display_year = int(round(y0 + alpha * (y1 - y0)))
            # How far through the whole animation we are (0 to 1); drives the ring.
            progress = (idx + alpha) / max(len(years) - 1, 1)

            # Sort ascending and keep the top N. Ascending order means the biggest
            # club gets the highest y_pos, so it appears at the TOP of the chart.
            top_clubs = vals.sort_values(ascending=True).tail(top_n)
            frame_rows = []
            for rank_pos, (club, val) in enumerate(top_clubs.items()):
                frame_rows.append({
                    "club": club,
                    "value": float(val),
                    "y_pos": rank_pos,  # vertical position = rank in this frame
                    "color": colors.get(club, "#3b82f6"),  # default blue if no colour
                    # "crest": crests.get(club, ""), #No club logas
                })
            frames.append({
                "year": display_year,
                "progress": progress,
                "rows": frame_rows,
            })

    # Add one last frame showing the exact final-year values (alpha = 1.0 is
    # never reached inside the loop above).
    last_year = years[-1]
    last_vals = pivoted.loc[last_year].fillna(0.0).sort_values(ascending=True).tail(top_n)
    frames.append({
        "year": int(last_year),
        "progress": 1.0,
        "rows": [
            {
                "club": club,
                "value": float(val),
                "y_pos": rank_pos,
                "color": colors.get(club, "#3b82f6"),
                # "crest": crests.get(club, ""),
            }
            for rank_pos, (club, val) in enumerate(last_vals.items())
        ],
    })
    return frames


def create_race_animation(df, output_path="club_revenue_race.gif", fps=24):
    frames = interpolate_frames(df)
    # crest_cache = {}  # so each crest image is loaded from disk only once #Removed the club logos
    if not frames: # Checks that frames is not empty
        raise ValueError("interpolate_frames(df) returned 0 frames; check input data and year sorting.")

    # Tall figure (10 x 12 inches at 120 dpi = 1200 x 1440 pixels) with a beige background.
    fig, ax = plt.subplots(figsize=(10, 12), dpi=120)
    bg_color = "#dedbd2"
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    def draw_frame(frame):
        """Redraw the whole chart for one frame."""
        ax.clear()  # wipe the previous frame
        ax.set_facecolor(bg_color)
        rows = frame["rows"]

        # Leave 35% headroom to the right of the longest bar for labels and the ring.
        max_val = max((r["value"] for r in rows), default=100.0) * 1.35

        y_positions = [r["y_pos"] for r in rows]
        values = [r["value"] for r in rows]
        bar_colors = [r["color"] for r in rows]

        # Draw all the horizontal bars at once.
        ax.barh(y_positions, values, height=0.72, color=bar_colors, edgecolor="none")

        for r in rows:
            y = r["y_pos"]
            val = r["value"]
            club = r["club"]

            # Left club label, right-aligned just outside the left edge of the bar.
            ax.text(
                -max_val * 0.02,
                y,
                club,
                va="center",
                ha="right",
                fontsize=11,
                fontweight="bold",
                color="#222222",
            )

            # Formatted revenue value to the right of each bar
            text_x = val + max_val * 0.02

            # Revenue label, e.g. "€ 818.10 M"
            ax.text(
                text_x,
                y,
                f"€ {val:,.2f} M",
                va="center",
                ha="left",
                fontsize=11,
                fontweight="bold",
                color="#1f2937",
            )

            ax.text(
                text_x,
                y,
                f"€ {val:,.2f} M",
                va="center",
                ha="left",
                fontsize=11,
                fontweight="bold",
                color="#1f2937",
            )

        # Year ring indicator in upper-right area
        ring_center_x = max_val * 0.92
        ring_center_y = len(rows) - 2.2
        ring_radius = 1.35

        # Grey full circle = the "track".
        # NOTE: Arc sizes are in DATA units. The x axis spans ~1,600 units (revenue)
        # while the y axis spans ~15 units (rank), so a width/height of 2.7 gives a
        # very thin, tall ellipse rather than a round ring. See the summary for a fix.
        bg_ring = Arc(
            (ring_center_x, ring_center_y),
            width=ring_radius * 2,
            height=ring_radius * 2,
            angle=0,
            theta1=0,
            theta2=360,
            lw=5,
            color="#b8b4aa",
        )
        # Dark arc on top = the "progress". Starts at 12 o'clock (angle=90) and
        # sweeps clockwise (negative theta2) as the animation progresses.
        # fg_ring = Arc(
        #     (ring_center_x, ring_center_y),
        #     width=ring_radius * 2,
           # height=ring_radius * 2,
             # angle=90,
            # theta1=0,
            # Clean year indicator in the upper-right corner (axes coordinates)
        ax.text(
                0.96,
                0.92,
                str(int(round(frame["year"]))),
                transform=ax.transAxes,
                ha="right",
                va="top",
                fontsize=28,
                fontweight="bold",
                color="#1f2937",
                bbox=dict(
                    boxstyle="round,pad=0.35",
                    facecolor="#ffffff",
                    edgecolor="#cbd5e1",
                    linewidth=1.5,
                    alpha=0.92,
                ),
            )


# Axis limits leave space on the left for club names and the right for labels.
        ax.set_xlim(-max_val * 0.28, max_val * 1.32)
        ax.set_ylim(-0.8, len(rows) - 0.2)
        ax.axis("off")  # hide axis lines, ticks and numbers
        plt.tight_layout()

    # Call `draw_frame` once per item in `frames`; interval is milliseconds per frame.
    anim = animation.FuncAnimation(fig, draw_frame, frames=frames, interval=1000 / fps)

    try:
        # Choose the file writer based on the output extension.
        if output_path.endswith(".mp4"):
            writer = animation.FFMpegWriter(fps=fps, bitrate=2500)  # needs ffmpeg installed
            anim.save(output_path, writer=writer)
        else:
            writer = animation.PillowWriter(fps=fps)  # GIF, no extra software needed
            anim.save(output_path, writer=writer)
    finally:
        plt.close(fig)

    print(f"Saved animation to {output_path}")


if __name__ == "__main__":
    df = build_sample_data()
    # To load from CSV instead: df = pd.read_csv("club_revenues.csv")
    # (needs columns: year, club, revenue_m, color, crest_path)
    create_race_animation(df, output_path="club_revenue_race.gif", fps=20)


"""
import io
import os

os.environ.setdefault("MPLBACKEND", "Agg")

from flask import Flask, request, send_file
import matplotlib

matplotlib.use("Agg")

from datavisualizer import build_sample_data, create_race_animation
import tempfile

app = Flask(__name__)


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
app.run(host="0.0.0.0", port=5000, debug=True)
"""
