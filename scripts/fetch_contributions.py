import json
import os
import re
from collections import defaultdict
from datetime import date

import requests
from bs4 import BeautifulSoup

USERNAME = "abhijeet-rx"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUTPUT = "data/contributions.json"

response = requests.get(
    URL,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30,
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")
pattern = re.compile(r"([\d,]+) contribution(?:s)?")

days = []
for cell in soup.select("td.ContributionCalendar-day"):
    iso = cell.get("data-date")
    if not iso:
        continue

    github_level = int(cell.get("data-level") or 0)
    labels = [cell.get("aria-label", "")]
    labels.extend(tag.get("aria-label", "") for tag in cell.select("[aria-label]"))
    labels.extend(tag.get("title", "") for tag in cell.select("[title]"))

    count = None
    for label in labels:
        match = pattern.search(label or "")
        if match:
            count = int(match.group(1).replace(",", ""))
            break

    # GitHub's zero-level cells often expose "No contributions" instead
    # of a numeric count. A non-zero level without an accessible count is
    # kept usable by falling back to its level.
    if count is None:
        count = 0 if github_level == 0 else github_level

    days.append({
        "date": iso,
        "count": count,
        "github_level": github_level,
        "level": 0 if count == 0 else min(5, github_level + 1),
    })

days.sort(key=lambda item: item["date"])
counts = {item["date"]: item["count"] for item in days}

total = sum(counts.values())
contribution_dates = sorted(
    iso for iso, count in counts.items() if count > 0
)

today = date.today()
yesterday = date.fromordinal(today.toordinal() - 1)

if counts.get(today.isoformat(), 0) > 0:
    streak_end = today
elif counts.get(yesterday.isoformat(), 0) > 0:
    streak_end = yesterday
else:
    streak_end = None

current_streak = 0
if streak_end:
    cursor = streak_end
    while counts.get(cursor.isoformat(), 0) > 0:
        current_streak += 1
        cursor = date.fromordinal(cursor.toordinal() - 1)

longest_streak = 0
run = 0
previous = None

for iso in contribution_dates:
    current = date.fromisoformat(iso)
    if previous and (current - previous).days == 1:
        run += 1
    else:
        run = 1
    longest_streak = max(longest_streak, run)
    previous = current

best_day = max(
    days,
    key=lambda item: (item["count"], item["date"]),
    default={"date": None, "count": 0},
)

monthly_totals = defaultdict(int)
for item in days:
    monthly_totals[item["date"][:7]] += item["count"]

payload = {
    "username": USERNAME,
    "generated_at": date.today().isoformat(),
    "total": total,
    "current_streak": current_streak,
    "longest_streak": longest_streak,
    "best_day": {
        "date": best_day["date"],
        "count": best_day["count"],
    },
    "monthly_totals": dict(sorted(monthly_totals.items())),
    "days": days,
}

os.makedirs("data", exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as file:
    json.dump(payload, file, indent=2)
    file.write("\n")

print(f"Fetched {len(days)} days and {total:,} contributions for @{USERNAME}.")
