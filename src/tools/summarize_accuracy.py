#!/usr/bin/env python3
"""Run every season and summarise how closely the engine matched the committee.

For each data/<year>/ with a config.yaml and a following year holding reference
north/south_ranks.csv, run the ranking engine and compare. Writes:

  docs/accuracy_summary.md    markdown tables + per-season miss lists
  docs/accuracy_summary.png   bar/heat chart (needs matplotlib)

Usage:
  python src/tools/summarize_accuracy.py [--data data] [--out docs] [--no-png]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tsa.config import LEAGUES, load_config        # noqa: E402
from tsa.data import load_season                   # noqa: E402
from tsa.ranking import rank_season                # noqa: E402
from tsa.report import compare                     # noqa: E402


def run_all(data_dir: Path) -> list[dict]:
    rows = []
    for season_dir in sorted(p for p in data_dir.iterdir() if p.is_dir() and (p / "config.yaml").is_file()):
        year = int(season_dir.name)
        ref = data_dir / str(year + 1) / "input"
        if not (ref / "north_ranks.csv").is_file():
            continue
        try:
            cfg = load_config(season_dir)
            season = load_season(cfg)
        except (FileNotFoundError, ValueError) as e:
            print(f"skip {year}: {e}", file=sys.stderr)
            continue
        stats = rank_season(season, cfg)
        res = compare(stats, ref, cfg.aliases)
        for league in LEAGUES:
            r = res.get(league)
            if r:
                rows.append({"year": year, "league": league, **r})
    return rows


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.0f}%" if b else "-"


def write_markdown(rows: list[dict], out: Path) -> None:
    lines = ["# Engine vs. committee: ranking accuracy by season", "",
             "Each row compares the engine's proposed ranks for season N+1 (computed from season N",
             "results) with the ranks the L&S committee actually approved. Weights were tuned on",
             "2026 only; earlier seasons are out-of-sample.", "",
             "| Season | League | Teams | Exact | Within 1 | Within 2 | Mean abs error | Worst miss | Spearman ρ |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['year']}→{r['year'] + 1} | {r['league']} | {r['n']} | {r['exact']} ({pct(r['exact'], r['n'])}) | "
                     f"{r['within1']} ({pct(r['within1'], r['n'])}) | {r['within2']} ({pct(r['within2'], r['n'])}) | "
                     f"{r['mae']:.2f} | {r['max']} | {r['rho']:.3f} |")
    # Totals per season
    lines += ["", "## Combined (North + South)", "", "| Season | Teams | Exact | Within 1 | Within 2 | Mean abs error | Worst miss |", "|---|---|---|---|---|---|---|"]
    for year in sorted({r["year"] for r in rows}):
        sub = [r for r in rows if r["year"] == year]
        n = sum(r["n"] for r in sub)
        ex, w1, w2 = (sum(r[k] for r in sub) for k in ("exact", "within1", "within2"))
        mae = sum(r["mae"] * r["n"] for r in sub) / n
        lines.append(f"| {year}→{year + 1} | {n} | {ex} ({pct(ex, n)}) | {w1} ({pct(w1, n)}) | {w2} ({pct(w2, n)}) | {mae:.2f} | {max(r['max'] for r in sub)} |")
    n = sum(r["n"] for r in rows)
    ex, w1, w2 = (sum(r[k] for r in rows) for k in ("exact", "within1", "within2"))
    mae = sum(r["mae"] * r["n"] for r in rows) / n
    lines.append(f"| **All** | {n} | {ex} ({pct(ex, n)}) | {w1} ({pct(w1, n)}) | {w2} ({pct(w2, n)}) | {mae:.2f} | {max(r['max'] for r in rows)} |")

    lines += ["", "## Teams the engine placed differently", "",
              "`committee → engine` rank; positive diff = engine ranked the team lower (bigger number)."]
    for r in rows:
        diffs = [d for d in r["diffs"] if d[3]]
        extra = ""
        if r["only_ref"]:
            extra = f" (in committee list only: {', '.join(r['only_ref'])})"
        lines += ["", f"### {r['year']}→{r['year'] + 1} {r['league']} — {len(diffs)} of {r['n']} differ{extra}", ""]
        for name, ours, ref, d in sorted(diffs, key=lambda x: -abs(x[3])):
            lines.append(f"- {name}: {ref} → {ours} ({d:+d})")
    out.write_text("\n".join(lines) + "\n")


def write_png(rows: list[dict], out: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    years = sorted({r["year"] for r in rows})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    width = 0.38
    for ax, league in zip(axes, LEAGUES):
        sub = {r["year"]: r for r in rows if r["league"] == league}
        xs = range(len(years))
        ex = [100 * sub[y]["exact"] / sub[y]["n"] if y in sub else 0 for y in years]
        w1 = [100 * sub[y]["within1"] / sub[y]["n"] if y in sub else 0 for y in years]
        w2 = [100 * sub[y]["within2"] / sub[y]["n"] if y in sub else 0 for y in years]
        ax.bar([x - width for x in xs], ex, width, label="exact")
        ax.bar(xs, w1, width, label="within 1")
        ax.bar([x + width for x in xs], w2, width, label="within 2")
        for x, y in zip(xs, years):
            if y in sub:
                ax.text(x, 103, f"MAE {sub[y]['mae']:.2f}", ha="center", fontsize=8)
        ax.set_xticks(list(xs))
        ax.set_xticklabels([f"{y}→{y + 1}" for y in years])
        ax.set_ylim(0, 110)
        ax.set_ylabel("% of teams")
        ax.set_title(f"{league} League")
        ax.grid(axis="y", alpha=0.3)
    axes[0].legend(loc="lower left")
    fig.suptitle("Engine vs. committee ranking agreement (weights tuned on 2026 only)")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    return True


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, default=Path("data"))
    p.add_argument("--out", type=Path, default=Path("docs"))
    p.add_argument("--no-png", action="store_true")
    args = p.parse_args(argv)

    rows = run_all(args.data)
    if not rows:
        print("no seasons with a following-year reference found", file=sys.stderr)
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    md = args.out / "accuracy_summary.md"
    write_markdown(rows, md)
    print(f"wrote {md}")
    if not args.no_png:
        png = args.out / "accuracy_summary.png"
        if write_png(rows, png):
            print(f"wrote {png}")
        else:
            print("matplotlib not installed; skipped PNG (pip install matplotlib)")
    for r in rows:
        print(f"{r['year']}→{r['year'] + 1} {r['league']:5s}: {r['exact']:2d}/{r['n']} exact, {r['within1']:2d} within 1, "
              f"MAE {r['mae']:.2f}, max {r['max']}, rho {r['rho']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
