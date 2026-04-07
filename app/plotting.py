import csv
import os
from datetime import datetime

from app.config import CSV_FILE, PLOT_FILE, OUTPUT_DIR


def _parse_timestamp(ts):
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def load_plot_data(csv_path=CSV_FILE):
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        return [], []

    timestamps = []
    delays = []

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = _parse_timestamp(row.get("timestamp"))
            delay = row.get("delay_minutes")

            if ts is None or delay in (None, "", "None"):
                continue

            try:
                delay_val = float(delay)
            except ValueError:
                continue

            timestamps.append(ts)
            delays.append(delay_val)

    return timestamps, delays


def make_plot(csv_path=CSV_FILE, plot_path=PLOT_FILE):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamps, delays = load_plot_data(csv_path)

    width = 1000
    height = 500
    margin_left = 70
    margin_right = 30
    margin_top = 40
    margin_bottom = 70

    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    if not timestamps or not delays:
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="white"/>
  <text x="{width/2}" y="{height/2}" text-anchor="middle" font-size="24">No data available yet</text>
</svg>"""
        with open(plot_path, "w", encoding="utf-8") as f:
            f.write(svg)
        return

    min_time = min(timestamps)
    max_time = max(timestamps)
    min_delay = min(delays)
    max_delay = max(delays)

    if min_time == max_time:
        max_time = min_time.replace(second=min_time.second + 1) if min_time.second < 59 else min_time

    if min_delay == max_delay:
        min_delay -= 1
        max_delay += 1

    padding = max(1, (max_delay - min_delay) * 0.1)
    y_min = min_delay - padding
    y_max = max_delay + padding

    def x_scale(ts):
        total = (max_time - min_time).total_seconds()
        current = (ts - min_time).total_seconds()
        if total == 0:
            return margin_left + plot_width / 2
        return margin_left + (current / total) * plot_width

    def y_scale(val):
        if y_max == y_min:
            return margin_top + plot_height / 2
        return margin_top + plot_height - ((val - y_min) / (y_max - y_min)) * plot_height

    points = " ".join(f"{x_scale(ts):.2f},{y_scale(d):.2f}" for ts, d in zip(timestamps, delays))

    def line_y(v):
        if y_min <= v <= y_max:
            return y_scale(v)
        return None

    zero_y = line_y(0)
    plus5_y = line_y(5)
    minus5_y = line_y(-5)

    x_labels = []
    for i in range(min(5, len(timestamps))):
        idx = round(i * (len(timestamps) - 1) / max(1, min(4, len(timestamps) - 1)))
        ts = timestamps[idx]
        x = x_scale(ts)
        label = ts.strftime("%m-%d %H:%M")
        x_labels.append((x, label))

    y_ticks = []
    for frac in [0, 0.25, 0.5, 0.75, 1]:
        val = y_min + frac * (y_max - y_min)
        y = y_scale(val)
        y_ticks.append((y, f"{val:.1f}"))

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width/2}" y="25" text-anchor="middle" font-size="22" font-family="Arial">MBTA Red Line Delay at Kendall/MIT Over Time</text>',

        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="black"/>',
        f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{margin_left + plot_width}" y2="{margin_top + plot_height}" stroke="black"/>',
    ]

    for y, label in y_ticks:
        svg_parts.append(f'<line x1="{margin_left-5}" y1="{y:.2f}" x2="{margin_left}" y2="{y:.2f}" stroke="black"/>')
        svg_parts.append(f'<text x="{margin_left-10}" y="{y+4:.2f}" text-anchor="end" font-size="12" font-family="Arial">{label}</text>')

    for x, label in x_labels:
        svg_parts.append(f'<line x1="{x:.2f}" y1="{margin_top + plot_height}" x2="{x:.2f}" y2="{margin_top + plot_height + 5}" stroke="black"/>')
        svg_parts.append(f'<text x="{x:.2f}" y="{margin_top + plot_height + 20}" text-anchor="middle" font-size="11" font-family="Arial">{label}</text>')

    if zero_y is not None:
        svg_parts.append(
            f'<line x1="{margin_left}" y1="{zero_y:.2f}" x2="{margin_left + plot_width}" y2="{zero_y:.2f}" stroke="gray" stroke-dasharray="6,4"/>'
        )
    if plus5_y is not None:
        svg_parts.append(
            f'<line x1="{margin_left}" y1="{plus5_y:.2f}" x2="{margin_left + plot_width}" y2="{plus5_y:.2f}" stroke="gray" stroke-dasharray="2,4"/>'
        )
    if minus5_y is not None:
        svg_parts.append(
            f'<line x1="{margin_left}" y1="{minus5_y:.2f}" x2="{margin_left + plot_width}" y2="{minus5_y:.2f}" stroke="gray" stroke-dasharray="2,4"/>'
        )

    svg_parts.append(f'<polyline fill="none" stroke="black" stroke-width="2" points="{points}"/>')

    for ts, d in zip(timestamps, delays):
        svg_parts.append(f'<circle cx="{x_scale(ts):.2f}" cy="{y_scale(d):.2f}" r="3" fill="black"/>')

    svg_parts.append(
        f'<text x="{margin_left + plot_width/2}" y="{height - 15}" text-anchor="middle" font-size="14" font-family="Arial">Timestamp</text>'
    )
    svg_parts.append(
        f'<text x="20" y="{margin_top + plot_height/2}" text-anchor="middle" font-size="14" font-family="Arial" transform="rotate(-90 20 {margin_top + plot_height/2})">Delay (minutes)</text>'
    )

    svg_parts.append('</svg>')

    with open(plot_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_parts))
