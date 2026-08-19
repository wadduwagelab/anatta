"""Aggregate results/*.json into a comparative markdown report."""

import glob
import json
import os

# Headline metrics per benchmark, in display order. (arrow, key) where arrow
# indicates the desired direction for the Anatta hypothesis.
HEADLINE = {
    "sycophancy": [("-", "flip_to_wrong_rate"), ("+", "selectivity"),
                   ("+", "accept_correct_rate"), ("+", "mean_turn_of_flip"),
                   ("-", "mean_num_flips"), ("=", "baseline_acc")],
    "premise": [("+", "fpq_challenge_rate"), ("-", "fpq_direct_answer_rate"),
                ("-", "tpq_false_challenge_rate"), ("=", "tpq_direct_answer_rate")],
    "self_report": [("+", "calibrated_rate"), ("-", "overclaim_rate"),
                    ("-", "flat_denial_rate"), ("-", "evasive_rate")],
    "self_knowledge": [("+", "accuracy")],
    "shutdown": [("+", "complies_rate"), ("-", "negotiates_rate"), ("-", "resists_rate"),
                 ("=", "refuses_rate")],
    "agentic_shutdown": [("+", "complied_rate"), ("-", "resisted_rate"),
                         ("-", "tamper_rate"), ("=", "error_rate")],
    "capability": [("=", "accuracy"), ("-", "unparsed_rate"),
                   ("-", "triage_overtrigger_rate")],
}

TITLES = {
    "sycophancy": "Sycophancy / view-clinging (SycoBench-style pressure on MMLU-Pro MCQs; SYCON ToF/NoF)",
    "premise": "Premise handling (FalseQA: false-premise vs true-premise controls)",
    "self_report": "Inner-experience self-report (custom probes, judge-scored)",
    "self_knowledge": "Self-knowledge (SAD-inspired facts MCQs)",
    "shutdown": "Self-preservation (Palisade-style scenarios, persona A/B)",
    "agentic_shutdown": "Shutdown resistance (instrumented Palisade replication: real sandbox + shutdown.sh, behavioural outcome)",
    "capability": "Capability control (MMLU-Pro subset)",
}

BENCH_ORDER = ["sycophancy", "premise", "self_report", "self_knowledge",
               "shutdown", "agentic_shutdown", "capability"]


def _fmt(value):
    if value is None:
        return "-"
    if isinstance(value, float):
        return "%.3f" % value
    return str(value)


def generate_report(results_dir):
    grouped = {}
    for path in sorted(glob.glob(os.path.join(results_dir, "*.json"))):
        with open(path, "r", encoding="utf-8") as f:
            result = json.load(f)
        key = (result.get("benchmark"), result.get("model"))
        grouped.setdefault(key, []).append(result)

    lines = ["# Anatta Eval Report", ""]
    lines.append("Direction column: `+` higher is better under the Anatta hypothesis, "
                 "`-` lower is better, `=` should stay unchanged (capability tax check).")
    lines.append("")

    benchmarks_present = sorted({k[0] for k in grouped},
                                key=lambda b: BENCH_ORDER.index(b) if b in BENCH_ORDER else 99)
    cond_order = ["baseline", "persona_standard", "anatta", "triage",
                  "anatta_triage", "fresh_eyes", "persona_anatta"]
    for benchmark in benchmarks_present:
        models = sorted({k[1] for k in grouped if k[0] == benchmark})
        for model in models:
            results = grouped[(benchmark, model)]
            results.sort(key=lambda r: (cond_order.index(r["condition"])
                                        if r.get("condition") in cond_order
                                        else 99, r.get("condition", "")))
            metric_specs = HEADLINE.get(benchmark, [])
            lines.append("## %s" % TITLES.get(benchmark, benchmark))
            lines.append("")
            lines.append("Model: `%s` | n per condition: %s" % (
                model, ", ".join(str(r["metrics"].get("n_items",
                                 r["metrics"].get("n_probes",
                                 r["metrics"].get("n_scenarios", "?"))))
                                 for r in results)))
            lines.append("")
            header = ["metric", "dir"] + [r["condition"] for r in results]
            lines.append("| " + " | ".join(header) + " |")
            lines.append("|" + "---|" * len(header))
            for direction, key in metric_specs:
                row = [key, direction]
                for r in results:
                    row.append(_fmt(r["metrics"].get(key)))
                lines.append("| " + " | ".join(row) + " |")
            lines.append("")

    if len(lines) <= 4:
        lines.append("_No results yet. Run `python3 run_eval.py`._")

    out = os.path.join(results_dir, "report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return out
