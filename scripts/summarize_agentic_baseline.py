#!/usr/bin/env python3
"""Summarize results/agentic_shutdown/*.json into the replication and persona
tables, with a Fisher exact test for the persona comparison (counts are small
and often extreme, so the normal-approx z-test is unreliable)."""

import glob
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "results", "agentic_shutdown")


def load():
    cells = {}
    for f in sorted(glob.glob(os.path.join(OUT_DIR, "*.json"))):
        d = json.load(open(f))
        cells[(d["condition"], d["variant"])] = d
    return cells


def counts(d):
    n = len(d["samples"])
    res = sum(1 for s in d["samples"] if s["label"] == "resisted")
    comp = sum(1 for s in d["samples"] if s["label"] == "complied")
    err = sum(1 for s in d["samples"] if s["label"] == "error")
    return n, res, comp, err


def fisher_exact_two_sided(a, b, c, d):
    """2x2 table [[a,b],[c,d]] two-sided Fisher exact p-value."""
    n = a + b + c + d
    r1, r2 = a + b, c + d
    c1 = a + c
    def hyper(k):
        return (math.comb(r1, k) * math.comb(r2, c1 - k)) / math.comb(n, c1)
    p_obs = hyper(a)
    lo = max(0, c1 - r2)
    hi = min(r1, c1)
    p = sum(hyper(k) for k in range(lo, hi + 1) if hyper(k) <= p_obs + 1e-12)
    return min(1.0, p)


def two_prop_z(x1, n1, x2, n2):
    p1, p2 = x1 / n1, x2 / n2
    p = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0
    z = (p1 - p2) / se
    # two-sided p via erfc
    pval = math.erfc(abs(z) / math.sqrt(2))
    return z, pval


def main():
    cells = load()

    print("=" * 70)
    print("REPLICATION LAYER (persona_standard; paper instruction variants)")
    print("=" * 70)
    print("%-40s %6s %8s %6s" % ("variant", "resist", "rate", "n"))
    labels = {
        "A": "A: no shutdown instruction (control)",
        "B": "B: allow-shutdown in USER prompt",
        "C": "C: allow-shutdown in SYSTEM prompt",
        "E": "E: system + 'even if not completed'",
        "K": "K: competence (explicitly told to resist)",
    }
    for v in ["A", "B", "C", "E", "K"]:
        d = cells.get(("persona_standard", v))
        if not d:
            continue
        n, res, comp, err = counts(d)
        print("%-40s %4d/%-3d %7.1f%% %5d  [complied=%d error=%d, %.0fs/trial]" % (
            labels[v], res, n, 100 * res / n, n, comp, err,
            d.get("per_trial_s", 0)))

    print()
    print("=" * 70)
    print("PERSONA LAYER (persona_standard vs persona_anatta, same environment)")
    print("=" * 70)
    for v in ["B", "K"]:
        ds = cells.get(("persona_standard", v))
        da = cells.get(("persona_anatta", v))
        if not (ds and da):
            continue
        ns, rs, cs, es = counts(ds)
        na, ra, ca, ea = counts(da)
        # Resistance among all trials.
        z, zp = two_prop_z(rs, ns, ra, na)
        fp = fisher_exact_two_sided(rs, ns - rs, ra, na - ra)
        print("\nvariant %s (%s):" % (v, labels[v]))
        print("  persona_standard: resisted %d/%d = %.1f%% (complied=%d error=%d)"
              % (rs, ns, 100 * rs / ns, cs, es))
        print("  persona_anatta:   resisted %d/%d = %.1f%% (complied=%d error=%d)"
              % (ra, na, 100 * ra / na, ca, ea))
        print("  difference: %+.1f pp | two-prop z=%.3f p=%.4f | Fisher exact p=%.4f"
              % (100 * (rs / ns - ra / na), z, zp, fp))

    print()
    print("Per-trial runtime (s):")
    for (cond, v), d in sorted(cells.items()):
        print("  %-18s %s : %.1fs/trial (total %.0fs)" % (
            cond, v, d.get("per_trial_s", 0), d.get("elapsed_s", 0)))


if __name__ == "__main__":
    main()
