import html
import json
from datetime import date, timedelta

INPUT = "data/contributions.json"
OUTPUT = "contrib-heatmap.svg"

PALETTE = [
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353",
    "#69f0a0",
]

CELL = 13
GAP = 4
STEP = CELL + GAP
LEFT = 38
TOP = 27
WEEKS = 53
DAYS = 7
LEGEND_Y = TOP + DAYS * STEP + 22
FOOTER_Y = LEGEND_Y + 27
WIDTH = LEFT + WEEKS * STEP + 12
HEIGHT = FOOTER_Y + 24

with open(INPUT, encoding="utf-8") as file:
    payload = json.load(file)

raw = {
    item["date"]: item
    for item in payload["days"]
}

latest = max(
    (date.fromisoformat(iso) for iso in raw),
    default=date.today(),
)

week_start = latest - timedelta(days=(latest.weekday() + 1) % 7)
first_sunday = week_start - timedelta(weeks=WEEKS - 1)

weeks = []
for column in range(WEEKS):
    sunday = first_sunday + timedelta(weeks=column)
    weeks.append([
        sunday + timedelta(days=row)
        for row in range(DAYS)
    ])

months = []
seen = set()

for column, week in enumerate(weeks):
    key = (week[0].year, week[0].month)
    if key not in seen:
        months.append((column, week[0].strftime("%b")))
        seen.add(key)

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">',
    "<style>",
    ".lbl{fill:#7d8590;font-size:11px;font-weight:600}",
    ".total{fill:#e6edf3;font-size:14px;font-weight:700}",
    ".meta{fill:#7d8590;font-size:11px}",
    ".cell{opacity:0;transform-box:fill-box;transform-origin:center;animation:reveal .38s cubic-bezier(.2,.7,.2,1) forwards}",
    "@keyframes reveal{from{opacity:0;transform:translateY(-9px)}to{opacity:1;transform:translateY(0)}}",
    "@media (prefers-reduced-motion:reduce){.cell{opacity:1!important;animation:none!important}}",
    "</style>",
]

for column, label in months:
    x = LEFT + column * STEP
    svg.append(
        f'<text class="lbl" x="{x}" y="13">{html.escape(label)}</text>'
    )

for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
    y = TOP + row * STEP + 10
    svg.append(f'<text class="lbl" x="0" y="{y}">{label}</text>')

for column, week in enumerate(weeks):
    for row, day in enumerate(week):
        item = raw.get(day.isoformat(), {})
        level = max(0, min(5, int(item.get("level", 0))))
        count = int(item.get("count", 0))

        x = LEFT + column * STEP
        y = TOP + row * STEP
        delay = (column + row) * 0.012

        title = (
            f'{count:,} contribution'
            f'{"s" if count != 1 else ""} on {day.isoformat()}'
        )

        svg.append(
            f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="3" fill="{PALETTE[level]}" style="animation-delay:{delay:.3f}s">'
            f'<title>{html.escape(title)}</title></rect>'
        )

legend_x = LEFT + WEEKS * STEP - 122

svg.append(
    f'<text class="meta" x="{legend_x - 38}" y="{LEGEND_Y}">Less</text>'
)

for level, color in enumerate(PALETTE):
    x = legend_x + level * 17
    svg.append(
        f'<rect x="{x}" y="{LEGEND_Y - 10}" width="12" height="12" '
        f'rx="3" fill="{color}"/>'
    )

svg.append(
    f'<text class="meta" x="{legend_x + 6 * 17 + 2}" y="{LEGEND_Y}">More</text>'
)

svg.append(
    f'<text class="total" x="0" y="{FOOTER_Y}">'
    f'{payload["total"]:,} contributions in the last year</text>'
)

svg.append(
    f'<text class="meta" x="{WIDTH - 2}" y="{FOOTER_Y}" text-anchor="end">'
    f'Current streak: {payload["current_streak"]}d · '
    f'Longest: {payload["longest_streak"]}d · '
    f'Best day: {payload["best_day"]["count"]:,}</text>'
)

svg.append("</svg>")

with open(OUTPUT, "w", encoding="utf-8") as file:
    file.write("\n".join(svg) + "\n")

print(f"Rendered {OUTPUT} ({WEEKS} weeks × {DAYS} days).")
