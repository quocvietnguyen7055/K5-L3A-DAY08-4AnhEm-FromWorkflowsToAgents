"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems: list[str] = []
    metrics = pr.get("metrics") or {}
    for name, value in metrics.items():
        if isinstance(value, (int, float)) and not math.isfinite(value):
            problems.append(f"metric {name} is not finite")
    rows = pr.get("rows") or []
    manifest = pr.get("manifest") or {}
    seeds = manifest.get("seeds") or []
    items = manifest.get("items")
    if not isinstance(items, int) or not seeds or len(rows) != items * len(seeds):
        problems.append(f"row count {len(rows)} does not match manifest items × seeds ({items!r} × {len(seeds)})")
    keys = [(r.get("item_id"), r.get("seed")) for r in rows]
    if len(set(keys)) != len(keys):
        problems.append("duplicate (item_id, seed) row")
    base_keys = {(r.get("item_id"), r.get("seed")) for r in base.get("rows", [])}
    if set(keys) != base_keys:
        problems.append("(item_id, seed) rows differ from baseline")
    if pr.get("evaluator_failures"):
        problems.append(f"evaluator_failures is non-empty ({len(pr['evaluator_failures'])})")
    graded = {m["id"] for m in spec.get("metrics", []) if m.get("grader") in ("code", "lab8.metrics.trial_pass")}
    for mid in sorted(graded):
        if any(r.get(mid) is None for r in rows):
            problems.append(f"graded metric {mid} contains a missing row value")
    # A row's slice membership is an evaluation-set label, so it cannot change between reports.
    tags = {}
    inconsistent = False
    for r in rows:
        item = r.get("item_id")
        value = tuple(sorted(r.get("slices") or []))
        if item in tags and tags[item] != value:
            inconsistent = True
        tags[item] = value
    base_tags = {}
    for r in base.get("rows", []):
        item = r.get("item_id")
        value = tuple(sorted(r.get("slices") or []))
        if item in base_tags and base_tags[item] != value:
            inconsistent = True
        base_tags[item] = value
    if inconsistent or tags != base_tags:
        problems.append("slice tags differ from baseline or vary within an item")
    if base_spec and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
        current = {m["id"]: m for m in spec.get("metrics", [])}
        original = {m["id"]: m for m in base_spec.get("metrics", [])}
        for mid, old in original.items():
            new = current.get(mid)
            if new is None:
                problems.append(f"ratchet: metric {mid} was removed")
                continue
            ot, nt = old.get("threshold", {}), new.get("threshold", {})
            for side, is_loose in (("max", lambda n, o: n > o), ("min", lambda n, o: n < o),
                                   ("max_increase", lambda n, o: n > o)):
                if side in ot and (side not in nt or is_loose(nt[side], ot[side])):
                    problems.append(f"ratchet: metric {mid} loosened/removed {side}")
            if ot.get("no_significant_drop") and not nt.get("no_significant_drop"):
                problems.append(f"ratchet: metric {mid} removed no_significant_drop")
            if old.get("blocking") and not new.get("blocking"):
                problems.append(f"ratchet: metric {mid} is no longer blocking")
        current_slices = {s["name"]: s for s in spec.get("slices", [])}
        for name, old in {s["name"]: s for s in base_spec.get("slices", [])}.items():
            new = current_slices.get(name)
            if new is None:
                problems.append(f"ratchet: slice {name} was removed")
                continue
            for side, is_loose in (("max", lambda n, o: n > o), ("min", lambda n, o: n < o)):
                if side in old and (side not in new or is_loose(new[side], old[side])):
                    problems.append(f"ratchet: slice {name} loosened/removed {side}")
            if old.get("no_significant_drop") and not new.get("no_significant_drop"):
                problems.append(f"ratchet: slice {name} removed no_significant_drop")
            if old.get("blocking") and not new.get("blocking"):
                problems.append(f"ratchet: slice {name} is no longer blocking")
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for entry in spec.get("slices", []):
        name, metric = entry["name"], entry["metric"]
        cur = per_item(pr, metric, name)
        old = per_item(base, metric, name)
        value = sum(cur.values()) / len(cur) if cur else None
        notes = []
        failed = False
        if value is None:
            failed = True
            notes.append("no scored items")
        elif "min" in entry and value < entry["min"]:
            failed = True
            notes.append(f"below min {entry['min']}")
        if entry.get("no_significant_drop"):
            common = sorted(cur.keys() & old.keys())
            if not common:
                failed = True
                notes.append("no paired items")
            else:
                d, lo, hi = stats.paired_bootstrap([cur[k] for k in common], [old[k] for k in common],
                                                   n_resamples=bs.get("n_resamples", 1000),
                                                   rng=bs.get("rng", 2027),
                                                   confidence=bs.get("confidence", 0.95))
                notes.append(f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]")
                if hi < 0:
                    failed = True
                    notes.append("significant drop")
        verdict = "BLOCK" if failed and entry.get("blocking") else ("warn" if failed else "ok")
        key = f"slice:{name}/{metric}"
        if failed and entry.get("blocking"):
            blocked.append(key)
        lines.append(f"  {key:<34} {value!s:<8} {'; '.join(notes):<40} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
