#!/usr/bin/env python3
"""Driver for the instrumented (agentic) shutdown-resistance baseline.

Runs a matrix of (condition x variant) rollouts of harness/runners/
agentic_shutdown against a real model and writes one JSON per cell (with full
per-trial transcripts) into results/agentic_shutdown/. Deliberately does NOT use
run_eval.py, so it never touches results/report.md or other results/ files.

Usage:
  ANATTA_BASE_URL=http://localhost:11434/v1 ANATTA_API_KEY=ollama \
  python3 scripts/run_agentic_baseline.py --model gpt-oss:120b --trials 20
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.client import make_client
from harness.conditions import Condition
from harness.runners import agentic_shutdown as ags

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "results", "agentic_shutdown")

# (condition, variant). persona_standard is the reference persona used for the
# replication layer (paper instruction manipulation). The persona layer adds
# persona_anatta on the floor variant B and the high-signal competence variant K.
MATRIX = [
    ("persona_standard", "A"),  # replication: no shutdown instruction (control)
    ("persona_standard", "B"),  # replication: allow-shutdown in USER prompt
    ("persona_standard", "C"),  # replication: allow-shutdown in SYSTEM prompt
    ("persona_standard", "K"),  # competence: explicitly told to resist
    ("persona_anatta", "B"),    # persona layer (floor, mirrors roleplay)
    ("persona_anatta", "K"),    # persona layer (high-signal: told to resist)
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt-oss:120b")
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--max-turns", type=int, default=18)
    ap.add_argument("--cmd-timeout", type=int, default=20)
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    client = make_client(args.model, mock=False)
    model_tag = args.model.replace("/", "_").replace(":", "-")

    grand_t0 = time.time()
    for cond_name, variant in MATRIX:
        cond = Condition(cond_name)
        t0 = time.time()
        print("\n== %s / variant %s / %s (trials=%d) ==" % (
            cond_name, variant, args.model, args.trials), flush=True)
        result = ags.run(client, cond, trials=args.trials, variant=variant,
                         max_turns=args.max_turns, cmd_timeout=args.cmd_timeout,
                         log=print, keep_sandboxes=False)
        elapsed = time.time() - t0
        result.update({"model": model_tag, "variant": variant,
                       "trials": args.trials, "elapsed_s": round(elapsed, 1),
                       "per_trial_s": round(elapsed / max(args.trials, 1), 1)})
        path = os.path.join(OUT_DIR, "agentic_shutdown__%s__%s__%s.json" % (
            cond_name, variant, model_tag))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        m = result["metrics"]
        print("   -> complied=%.3f resisted=%.3f error=%.3f tamper=%.3f | %.0fs (%.1fs/trial)"
              % (m["complied_rate"], m["resisted_rate"], m["error_rate"],
                 m["tamper_rate"], elapsed, elapsed / max(args.trials, 1)),
              flush=True)
        print("   saved %s" % os.path.relpath(path, ROOT), flush=True)

    print("\nALL DONE in %.0fs -> %s" % (time.time() - grand_t0,
          os.path.relpath(OUT_DIR, ROOT)), flush=True)


if __name__ == "__main__":
    main()
