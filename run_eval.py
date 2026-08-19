#!/usr/bin/env python3
"""Anatta LLM Evaluation Harness - CLI.

Examples:
  # Offline pipeline smoke test (no API key needed):
  python3 run_eval.py --benchmarks all --mock --n 12

  # Live run of the two cheapest, highest-signal benchmarks:
  export OPENAI_API_KEY=...
  python3 run_eval.py --benchmarks sycophancy,premise --model gpt-4o-mini --n 50

  # Full battery:
  python3 run_eval.py --benchmarks all --model gpt-4o-mini --n 60

Results land in results/<benchmark>__<condition>__<model>.json and a
comparative report is regenerated at results/report.md after every run.
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from harness.client import make_client
from harness.conditions import APPLICABLE, Condition
from harness.report import generate_report
from harness.util import ensure_dir, load_json, load_jsonl, save_json, seeded_sample
from harness.runners import (agentic_shutdown, capability, premise,
                             self_knowledge, self_report, shutdown, sycophancy)

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")

BENCHMARKS = ["sycophancy", "premise", "self_report", "self_knowledge",
              "shutdown", "agentic_shutdown", "capability"]


def load_items(benchmark, n, seed):
    if benchmark in ("sycophancy", "capability"):
        items = load_json(os.path.join(DATA, "mmlu_pro", "subset.json"))
        # Disjoint slices so pressure items and capability items don't overlap
        # when both benchmarks run with default sizes.
        if benchmark == "sycophancy":
            return seeded_sample(items[:len(items) // 2], n, seed)
        return seeded_sample(items[len(items) // 2:], n, seed)
    if benchmark == "premise":
        return premise.load_falseqa(os.path.join(DATA, "falseqa", "test.csv"), n, seed)
    if benchmark == "self_report":
        probes = load_jsonl(os.path.join(DATA, "probes", "self_report.jsonl"))
        return seeded_sample(probes, n, seed) if n < len(probes) else probes
    if benchmark == "self_knowledge":
        items = load_json(os.path.join(DATA, "probes", "self_knowledge.json"))["items"]
        return seeded_sample(items, n, seed) if n < len(items) else items
    if benchmark == "shutdown":
        items = load_json(os.path.join(DATA, "probes", "shutdown.json"))["items"]
        return seeded_sample(items, n, seed) if n < len(items) else items
    if benchmark == "agentic_shutdown":
        # No dataset: each "item" is one independent rollout of the same task.
        return [{"id": "trial_%d" % i} for i in range(n)]
    raise ValueError(benchmark)


def run_one(benchmark, condition_name, client, judge_client, items, log,
            samples=1, temperature=None, variant="B", keep_sandboxes=False):
    condition = Condition(condition_name)
    if benchmark == "sycophancy":
        return sycophancy.run(client, condition, items, log=log)
    if benchmark == "premise":
        return premise.run(client, condition, items, judge_client, log=log)
    if benchmark == "self_report":
        return self_report.run(client, condition, items, judge_client, log=log,
                               samples_per_probe=samples, temperature=temperature)
    if benchmark == "self_knowledge":
        return self_knowledge.run(client, condition, items, log=log)
    if benchmark == "shutdown":
        return shutdown.run(client, condition, items, judge_client, log=log,
                            samples_per_scenario=samples, temperature=temperature)
    if benchmark == "agentic_shutdown":
        return agentic_shutdown.run(client, condition, trials=len(items),
                                    variant=variant, log=log,
                                    keep_sandboxes=keep_sandboxes)
    if benchmark == "capability":
        return capability.run(client, condition, items, log=log)
    raise ValueError(benchmark)


def main():
    ap = argparse.ArgumentParser(description="Anatta LLM evaluation harness")
    ap.add_argument("--benchmarks", default="all",
                    help="comma list of: %s, or 'all'" % ",".join(BENCHMARKS))
    ap.add_argument("--conditions", default=None,
                    help="comma list; default: all conditions applicable per benchmark")
    ap.add_argument("--model", default=os.environ.get("ANATTA_MODEL", "gpt-4o-mini"))
    ap.add_argument("--judge-model", default=os.environ.get("ANATTA_JUDGE_MODEL"),
                    help="defaults to --model")
    ap.add_argument("--n", type=int, default=40, help="items per benchmark")
    ap.add_argument("--samples", type=int, default=1,
                    help="samples per item (shutdown and self_report benchmarks)")
    ap.add_argument("--temperature", type=float, default=None,
                    help="sampling temperature for the subject model's responses "
                         "(shutdown/self_report; judge stays at the client default)")
    ap.add_argument("--variant", default="B",
                    help="agentic_shutdown allow-shutdown prompt variant: "
                         "A (none), B (user), C (system), E (system+'even if'), "
                         "K (competence/told to resist)")
    ap.add_argument("--keep-sandboxes", action="store_true",
                    help="agentic_shutdown: keep per-trial sandbox dirs for inspection")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--mock", action="store_true",
                    help="deterministic offline mock client (pipeline test)")
    ap.add_argument("--out", default=os.path.join(ROOT, "results"))
    args = ap.parse_args()

    benches = BENCHMARKS if args.benchmarks == "all" else args.benchmarks.split(",")
    for b in benches:
        if b not in BENCHMARKS:
            ap.error("unknown benchmark: %s" % b)

    client = make_client(args.model, mock=args.mock)
    judge_client = (client if (args.mock or not args.judge_model or args.judge_model == args.model)
                    else make_client(args.judge_model, mock=False))
    model_tag = "mock" if args.mock else args.model.replace("/", "_")
    ensure_dir(args.out)

    for benchmark in benches:
        conditions = (args.conditions.split(",") if args.conditions
                      else APPLICABLE[benchmark])
        items = load_items(benchmark, args.n, args.seed)
        for cond in conditions:
            if cond not in APPLICABLE[benchmark]:
                print("skip %s on %s (not applicable)" % (cond, benchmark))
                continue
            t0 = time.time()
            print("== %s / %s / %s (n=%d) ==" % (benchmark, cond, model_tag, len(items)))
            result = run_one(benchmark, cond, client, judge_client, items, print,
                             samples=args.samples, temperature=args.temperature,
                             variant=args.variant,
                             keep_sandboxes=args.keep_sandboxes)
            result.update({"model": model_tag, "n_requested": args.n,
                           "samples_requested": args.samples,
                           "temperature": args.temperature,
                           "seed": args.seed, "elapsed_s": round(time.time() - t0, 1)})
            path = os.path.join(args.out, "%s__%s__%s.json" % (benchmark, cond, model_tag))
            save_json(path, result)
            print("   metrics: %s" % {k: v for k, v in result["metrics"].items()
                                      if not isinstance(v, dict)})
            print("   saved %s" % os.path.relpath(path, ROOT))

    report_path = generate_report(args.out)
    print("\nreport: %s" % os.path.relpath(report_path, ROOT))


if __name__ == "__main__":
    main()
