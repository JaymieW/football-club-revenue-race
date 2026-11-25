"""
Animated "bar chart race" of football club revenues.

What it does:
1. Builds a table of club revenues across years (in EUR millions).
2. Interpolates smooth in-between frames so bars move smoothly instead of jumping.
3. Renders each frame as a horizontal bar chart with club names on the left,
   formatted revenue values on the right, and a year badge in the top-right.
4. Saves the frames as an animated GIF (using Pillow) or MP4 (using FFmpeg),
   then cleans up Matplotlib/animation objects to stay within tight RAM limits.
"""

import gc
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from PIL import Image


def load_crest(path, zoom=0.22):
    """Safely open an image file as RGBA if it exists; otherwise return None."""
    if path and os.path.exists(path):
        return Image.open(path).convert("RGBA")
    return None


def build_sample_data():
    """Create sample revenue data (in € millions) for clubs across 2016–2018."""
    rows = [
        # 2016 figures
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
        # 2017 figures
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
        # 2018 figures
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


def interpolate_frames(df, steps_per_year=20, top_n=15):
    """
    Build smooth intermediate frames between consecutive years.

    Using 20 steps_per_year instead of 65 keeps the total frame count compact
    so Pillow uses significantly less RAM during GIF encoding.
    """
    # Average duplicate (year, club) entries if any exist before pivoting
    clean_df = df.groupby(["year", "club"], as_index=False)["revenue_m"].mean()
    years = sorted(clean_df["year"].unique())

    # Pivot to rows = years, columns = clubs, and interpolate any missing values
    pivoted = (
        clean_df.pivot(index="year", columns="club", values="revenue_m")
        .reindex(years)
        .interpolate(method="linear")
    )

    # Map each club to its assigned bar color
    colors = df.drop_duplicates("club").set_index("club")["color"].to_dict()
    frames = []

    # Blend values between each pair of consecutive years (e.g., 2016->2017, 2017->2018)
    for idx in range(len(years) - 1):
        y0, y1 = years[idx], years[idx + 1]
        v0 = pivoted.loc[y0].fillna(0.0)
        v1 = pivoted.loc[y1].fillna(0.0)

        for step in range(steps_per_year):
            alpha = step / steps_per_year  # Blend factor from 0.0 toward 1.0
            vals = v0 * (1 - alpha) + v1 * alpha

            # Nearest year for the badge and overall progress (0.0 to 1.0)
            display_year = int(round(y0 + alpha * (y1 - y0)))
            progress = (idx + alpha) / max(len(years) - 1, 1)

            # Ascending sort puts largest revenue at the top y_pos on a horizontal bar chart
            top_clubs = vals.sort_values(ascending=True).tail(top_n)
            frame_rows = [
                {
                    "club": club,
                    "value": float(val),
                    "y_pos": rank_pos,
                    "color": colors.get(club, "#3b82f6"),
                }
                for rank_pos, (club, val) in enumerate(top_clubs.items())
            ]
            frames.append({
                "year": display_year,
                "progress": progress,
                "rows": frame_rows,
            })

    # Append a final frame at 100% of the last year's values
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
            }
            for rank_pos, (club, val) in enumerate(last_vals.items())
        ],
    })
    return frames


def create_race_animation(df, output_path="club_revenue_race.gif", fps=12, steps_per_year=20):
    """Render all frames to a GIF (or MP4) using a low-memory figure size and DPI."""
    frames = interpolate_frames(df, steps_per_year=steps_per_year)
    if not frames:
        raise ValueError("interpolate_frames(df) returned 0 frames; check input data and year sorting.")

    # 7.5 x 8.5 inches at 80 DPI = 600 x 680 px (much lighter on RAM than 1200 x 1440 px)
    fig, ax = plt.subplots(figsize=(7.5, 8.5), dpi=80)
    bg_color = "#dedbd2"
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    def draw_frame(frame):
        """Clear previous plot elements and draw one frame's bars, labels, and year badge."""
        ax.clear()
        ax.set_facecolor(bg_color)
        rows = frame["rows"]

        # Extra right-hand headroom gives space for revenue labels
        max_val = max((r["value"] for r in rows), default=100.0) * 1.35
        y_positions = [r["y_pos"] for r in rows]
        values = [r["value"] for r in rows]
        bar_colors = [r["color"] for r in rows]

        # Draw horizontal bars for all ranked clubs in this frame
        ax.barh(y_positions, values, height=0.72, color=bar_colors, edgecolor="none")

        # Add club names (left) and formatted revenue figures (right of each bar)
        for r in rows:
            y = r["y_pos"]
            val = r["value"]
            club = r["club"]

            ax.text(
                -max_val * 0.02,
                y,
                club,
                va="center",
                ha="right",
                fontsize=10,
                fontweight="bold",
                color="#222222",
            )

            ax.text(
                val + max_val * 0.02,
                y,
                f"€ {val:,.2f} M",
                va="center",
                ha="left",
                fontsize=10,
                fontweight="bold",
                color="#1f2937",
            )

        # Year badge in the upper-right corner using axes coordinates (0..1)
        ax.text(
            0.96,
            0.92,
            str(int(round(frame["year"]))),
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=24,
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

        # Pad x-axis for left-side club names and right-side values; hide axes chrome
        ax.set_xlim(-max_val * 0.28, max_val * 1.32)
        ax.set_ylim(-0.8, len(rows) - 0.2)
        ax.axis("off")
        plt.tight_layout()

    # Build the animation object across all interpolated frames
    anim = animation.FuncAnimation(fig, draw_frame, frames=frames, interval=1000 / fps)

    try:
        # Export as MP4 if requested, otherwise save as an animated GIF via Pillow
        if output_path.endswith(".mp4"):
            writer = animation.FFMpegWriter(fps=fps, bitrate=2500)
            anim.save(output_path, writer=writer)
        else:
            writer = animation.PillowWriter(fps=fps)
            anim.save(output_path, writer=writer)
    finally:
        # Always close figures, drop the animation reference, and run garbage collection
        plt.close("all")
        del anim
        gc.collect()

    print(f"Saved animation to {output_path}")


if __name__ == "__main__":
    # Run standalone to generate a local test GIF
    df = build_sample_data()
    create_race_animation(df, output_path="club_revenue_race.gif", fps=12, steps_per_year=20)