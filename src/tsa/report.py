"""Write ranking outputs and compare against a reference ranking."""

from __future__ import annotations

import csv
from pathlib import Path

from .config import LEAGUES, SeasonConfig
from .data import Season
from .ranking import TeamStats


def write_ranks(stats: dict[str, TeamStats], out_dir: Path) -> dict[str, Path]:
    """north_ranks.csv / south_ranks.csv in the same ``rank,team`` format the
    scheduler consumes, so this season's output is next season's input."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for league in LEAGUES:
        rows = sorted((s for s in stats.values() if s.league == league), key=lambda s: s.new_rank)
        p = out_dir / f"{league.lower()}_ranks.csv"
        with p.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["rank", "team"])
            w.writerows((s.new_rank, s.name) for s in rows)
        paths[league] = p
    return paths


def write_report(season: Season, stats: dict[str, TeamStats], cfg: SeasonConfig, out_dir: Path) -> Path:
    """ranking_report.csv: one row per team with every input to the rating."""
    p = out_dir / "ranking_report.csv"
    metric_names = [m.name for m in cfg.metrics]
    comp_keys = cfg.component_names
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["league", "new_rank", "prev_rank", "change", "team", "prev_division",
                    "div_record", "ovr_record", "div_pd", "ovr_pd", "div_winner", "div_loser",
                    *[f"m_{k}" for k in metric_names],
                    "rating", *[f"c_{k}" for k in comp_keys], "adjustments"])
        for league in LEAGUES:
            for s in sorted((s for s in stats.values() if s.league == league), key=lambda s: s.new_rank):
                w.writerow([
                    league, s.new_rank, s.prev_rank, s.prev_rank - s.new_rank, s.name, s.division,
                    s.div_record, s.ovr_record, f"{s.div_pd:g}", f"{s.ovr_pd:g}",
                    int(s.div_winner), int(s.div_loser),
                    *["" if k not in s.metrics else f"{s.metrics[k]:.2f}" for k in metric_names],
                    f"{s.rating:.1f}", *[f"{s.components.get(k, 0):.1f}" for k in comp_keys],
                    " | ".join(s.adjustments),
                ])
    return p


# ---------------------------------------------------------------------------

def load_reference(path: Path) -> dict[str, int]:
    with path.open(newline="", encoding="utf-8") as fh:
        return {r["team"].strip(): int(r["rank"]) for r in csv.DictReader(fh)}


def compare(stats: dict[str, TeamStats], ref_dir: Path, aliases: dict[str, str]) -> dict[str, dict]:
    """Compare computed new ranks with reference north/south_ranks.csv in ref_dir."""
    results = {}
    for league in LEAGUES:
        ref_path = ref_dir / f"{league.lower()}_ranks.csv"
        if not ref_path.is_file():
            continue
        ref = {aliases.get(k, k): v for k, v in load_reference(ref_path).items()}
        ours = {s.name: s.new_rank for s in stats.values() if s.league == league}
        common = sorted(set(ref) & set(ours), key=lambda n: ref[n])
        diffs = [(n, ours[n], ref[n], ours[n] - ref[n]) for n in common]
        abs_err = [abs(d[3]) for d in diffs]
        n = len(common)
        # Spearman rho on the common set.
        d2 = sum(d[3] ** 2 for d in diffs)
        rho = 1 - 6 * d2 / (n * (n * n - 1)) if n > 2 else float("nan")
        results[league] = {
            "n": n,
            "exact": sum(1 for e in abs_err if e == 0),
            "within1": sum(1 for e in abs_err if e <= 1),
            "within2": sum(1 for e in abs_err if e <= 2),
            "mae": sum(abs_err) / n if n else float("nan"),
            "max": max(abs_err) if abs_err else 0,
            "rho": rho,
            "diffs": diffs,
            "only_ours": sorted(set(ours) - set(ref)),
            "only_ref": sorted(set(ref) - set(ours)),
        }
    return results


def format_compare(results: dict[str, dict], show_diffs: bool = True) -> str:
    lines = []
    for league, r in results.items():
        lines.append(f"{league}: {r['exact']}/{r['n']} exact, {r['within1']} within 1, {r['within2']} within 2, "
                     f"MAE {r['mae']:.2f}, max {r['max']}, Spearman {r['rho']:.3f}")
        if r["only_ours"] or r["only_ref"]:
            lines.append(f"  only in ours: {r['only_ours']}  only in reference: {r['only_ref']}")
        if show_diffs:
            for name, ours, ref, d in r["diffs"]:
                if d:
                    lines.append(f"  {ref:3d} ref  {ours:3d} ours  {d:+3d}  {name}")
    return "\n".join(lines)
