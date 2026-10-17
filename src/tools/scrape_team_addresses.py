#!/usr/bin/env python3
"""Scrape club addresses from the TSA SwimTopia site into a CSV.

Reads the club list at https://tsa.swimtopia.com/roster (Northern / Southern
columns), visits each club page, and extracts the structured address and
lat/long from the Google Maps snippet (itemprop="address"/"geo"). If a page
has no map snippet, falls back to the first "<street>\\n<City, NC 12345>" pair
found in the page text and flags it in the note column.

Usage:
  python src/tools/scrape_team_addresses.py [--out data/<year>/input/team_addresses.csv]

Output columns: division, team, url, address, latitude, longitude, note

Fetching is done with curl rather than urllib because this host's TLS chain
trips Python's stricter certificate checks.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import subprocess
import sys
import time
from pathlib import Path

ROSTER_URL = "https://tsa.swimtopia.com/roster"
DELAY_SECONDS = 0.3
FIELDS = ["division", "team", "url", "address", "latitude", "longitude", "note"]


def fetch(url: str) -> str:
    return subprocess.run(
        ["curl", "-sL", "--max-time", "30", url],
        capture_output=True, text=True, check=True,
    ).stdout


def strip_tags(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def parse_roster(page: str) -> list[tuple[str, str, str]]:
    """Return (division, team, url) for every club linked on the roster page."""
    teams: list[tuple[str, str, str]] = []
    for row in re.findall(r'<tr class="club">(.*?)</tr>', page, re.S):
        cells = re.findall(r'<td class="club">(.*?)</td>', row, re.S)
        for division, cell in zip(("North", "South"), cells):
            # Some cells contain an empty <a> before the real one; take the first with text.
            for url, text in re.findall(r'href="([^"]+)"[^>]*>(.*?)</a>', cell, re.S):
                name = strip_tags(text)
                if name:
                    teams.append((division, name, url))
                    break
    return teams


def parse_club(page: str) -> tuple[str, str, str, str]:
    """Return (address, latitude, longitude, note) from a club page."""
    addr = re.search(r'itemprop="altitem">(.*?)</span>', page, re.S)
    lat = re.search(r'itemprop="latitude">(.*?)</span>', page)
    lon = re.search(r'itemprop="longitude">(.*?)</span>', page)
    if addr:
        return (
            strip_tags(addr.group(1)),
            lat.group(1).strip() if lat else "",
            lon.group(1).strip() if lon else "",
            "",
        )
    # Fallback: look for "<street>\n<City, NC 12345>" in visible text.
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", page, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", "\n", text))
    m = re.search(r"(\d{2,6} [^\n]+?)\s*\n\s*([A-Za-z .]+, NC \d{5})", text)
    if m:
        return (f"{m.group(1).strip()}, {m.group(2).strip()}, USA", "", "",
                "address from page text; no map widget")
    return ("", "", "", "no address found")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=Path("team_addresses.csv"), help="output CSV path")
    args = p.parse_args(argv)

    teams = parse_roster(fetch(ROSTER_URL))
    if not teams:
        print("error: no clubs found on roster page; site layout may have changed", file=sys.stderr)
        return 1
    print(f"{len(teams)} clubs linked from roster")

    rows = []
    for division, name, url in teams:
        try:
            address, lat, lon, note = parse_club(fetch(url))
        except subprocess.CalledProcessError as e:
            address, lat, lon, note = "", "", "", f"fetch failed: {e}"
        rows.append(dict(zip(FIELDS, (division, name, url, address, lat, lon, note))))
        time.sleep(DELAY_SECONDS)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    flagged = [r["team"] for r in rows if r["note"]]
    print(f"wrote {len(rows)} rows -> {args.out}")
    if flagged:
        print(f"{len(flagged)} row(s) flagged in note column: {flagged}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
