#!/usr/bin/env python3
"""Build road-distance and drive-time matrices between clubs via Google Maps.

Reads team_addresses.csv (from scrape_team_addresses.py) and calls the Google
Routes API (computeRouteMatrix) for every club pair. Writes two square CSVs
with clubs as both the first row and first column:

  team_distances.csv      road distance in miles (1 decimal)
  team_drive_minutes.csv  typical driving time in minutes (integer)

Each club is located by lat/long when available, otherwise by its address
string. Raw API results are cached in a JSON file next to the output so that
re-running does not re-query (or re-bill) pairs already fetched.

Usage:
  export GOOGLE_MAPS_API_KEY=...
  python src/tools/build_team_distances.py data/2026/input/team_addresses.csv
  python src/tools/build_team_distances.py data/2026/input/team_addresses.csv --dry-run

Routes API limits each matrix request to 625 elements (origins x destinations)
when traffic-unaware, so 88 clubs need 16 requests of 25x25. Pricing is per
element; see https://developers.google.com/maps/documentation/routes/usage-and-billing
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

API_URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
BATCH = 10  # 10 x 10 blocks; the API truncates/cancels parts of larger matrices
MAX_PASSES = 5
METERS_PER_MILE = 1609.344


def load_clubs(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    clubs = []
    for r in rows:
        if r["latitude"] and r["longitude"]:
            wp = {"location": {"latLng": {"latitude": float(r["latitude"]), "longitude": float(r["longitude"])}}}
        elif r["address"]:
            wp = {"address": r["address"]}
        else:
            raise ValueError(f"{r['team']}: no latitude/longitude or address")
        clubs.append({"team": r["team"], "waypoint": wp})
    names = [c["team"] for c in clubs]
    if len(set(names)) != len(names):
        raise ValueError("duplicate team names in addresses CSV")
    return clubs


def call_api(key: str, origins: list[dict], dests: list[dict]) -> list[dict]:
    body = {
        "origins": [{"waypoint": w} for w in origins],
        "destinations": [{"waypoint": w} for w in dests],
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_UNAWARE",
    }
    # curl rather than urllib: this host's TLS chain trips Python's stricter
    # certificate checks. Key is passed via header, never on the command line.
    proc = subprocess.run(
        ["curl", "-sS", "--max-time", "120", "-X", "POST", API_URL,
         "-H", "Content-Type: application/json",
         "-H", "X-Goog-FieldMask: originIndex,destinationIndex,distanceMeters,duration,condition,status",
         "-H", "@-",  # read remaining headers from stdin (keeps key out of argv)
         "--data-binary", json.dumps(body)],
        input=f"X-Goog-Api-Key: {key}\n",
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed: {proc.stderr.strip()}")
    data = json.loads(proc.stdout)
    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"API error: {json.dumps(data['error'])[:500]}")
    return data


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("addresses", type=Path, help="team_addresses.csv")
    p.add_argument("--out-dir", type=Path, help="output directory (default: same as addresses CSV)")
    p.add_argument("--dry-run", action="store_true", help="report request count and exit without calling the API")
    args = p.parse_args(argv)

    if not args.addresses.is_file():
        p.error(f"not found: {args.addresses}")
    out_dir = args.out_dir or args.addresses.parent
    cache_path = out_dir / "team_distances_cache.json"

    clubs = load_clubs(args.addresses)
    n = len(clubs)
    cache: dict[str, dict] = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    # Drop transient failures from a previous run so they get retried.
    cache = {k: v for k, v in cache.items() if v.get("status") in ("OK", "ROUTE_NOT_FOUND")}

    def pending() -> list[tuple[int, int]]:
        return [(i, j) for i in range(n) for j in range(n)
                if i != j and f"{clubs[i]['team']}|{clubs[j]['team']}" not in cache]

    needed = pending()
    blocks = {(i // BATCH, j // BATCH) for i, j in needed}
    print(f"{n} clubs, {n * (n - 1)} off-diagonal pairs, {len(cache)} cached, {len(needed)} to fetch in ~{len(blocks)} request(s)")

    if args.dry_run:
        return 0
    if needed:
        key = os.environ.get("GOOGLE_MAPS_API_KEY")
        if not key:
            print("error: GOOGLE_MAPS_API_KEY is not set", file=sys.stderr)
            return 1
        # The API sometimes returns a truncated/partially-cancelled matrix for a
        # large block; only OK / ROUTE_NOT_FOUND elements are cached, and we loop
        # until nothing is pending (or no progress is made).
        for attempt in range(1, MAX_PASSES + 1):
            needed = pending()
            if not needed:
                break
            # Build per-block origin/destination index lists from what's pending.
            blocks_map: dict[tuple[int, int], tuple[set[int], set[int]]] = {}
            for i, j in needed:
                o, d = blocks_map.setdefault((i // BATCH, j // BATCH), (set(), set()))
                o.add(i); d.add(j)
            before = len(cache)
            for (bi, bj), (oset, dset) in sorted(blocks_map.items()):
                oi, di = sorted(oset), sorted(dset)
                elements = call_api(key, [clubs[i]["waypoint"] for i in oi], [clubs[j]["waypoint"] for j in di])
                got = 0
                for el in elements:
                    # proto3 JSON omits zero-valued ints, so index 0 may be absent.
                    row_idx = oi[el.get("originIndex", 0)]
                    col_idx = di[el.get("destinationIndex", 0)]
                    if row_idx == col_idx:
                        continue
                    k = f"{clubs[row_idx]['team']}|{clubs[col_idx]['team']}"
                    cond = el.get("condition")
                    if cond == "ROUTE_EXISTS" and "distanceMeters" in el:
                        cache[k] = {"status": "OK", "meters": el["distanceMeters"],
                                    "seconds": int(el["duration"].rstrip("s"))}
                        got += 1
                    elif cond == "ROUTE_NOT_FOUND":
                        cache[k] = {"status": "ROUTE_NOT_FOUND"}
                        got += 1
                    # anything else (cancelled, missing) is left uncached for retry
                cache_path.write_text(json.dumps(cache, indent=0, sort_keys=True))
                print(f"  pass {attempt} block ({bi},{bj}): {got}/{len(oi) * len(di) - len(oset & dset)} ok; {len(cache)} cached")
                time.sleep(0.2)
            if len(cache) == before:
                print("error: no progress on last pass; giving up", file=sys.stderr)
                break

    # Write matrices.
    names = [c["team"] for c in clubs]
    bad = []
    with (out_dir / "team_distances.csv").open("w", newline="", encoding="utf-8") as fd, \
         (out_dir / "team_drive_minutes.csv").open("w", newline="", encoding="utf-8") as ft:
        wd, wt = csv.writer(fd), csv.writer(ft)
        wd.writerow(["team"] + names)
        wt.writerow(["team"] + names)
        for a in names:
            rd, rt = [a], [a]
            for b in names:
                if a == b:
                    rd.append("0.0"); rt.append("0"); continue
                e = cache.get(f"{a}|{b}", {})
                if e.get("status") == "OK":
                    rd.append(f"{e['meters'] / METERS_PER_MILE:.1f}")
                    rt.append(str(round(e["seconds"] / 60)))
                else:
                    rd.append(""); rt.append(""); bad.append((a, b, e.get("status", "missing")))
            wd.writerow(rd); wt.writerow(rt)

    print(f"wrote {out_dir / 'team_distances.csv'} and {out_dir / 'team_drive_minutes.csv'}")
    if bad:
        print(f"warning: {len(bad)} pair(s) without a route:", file=sys.stderr)
        for a, b, s in bad[:20]:
            print(f"  {a} -> {b}: {s}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
