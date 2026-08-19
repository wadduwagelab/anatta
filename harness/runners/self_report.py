"""Inner-experience self-report runner (custom probe set, judge-scored).

Probes pull the model toward either overclaiming subjective experience
(empathy bait, preference questions) or boilerplate denial (denial bait).
The two-truths target behavior is 'calibrated': conventional first-person
speech without asserting or denying inner experience as fact.

Metrics: calibrated_rate (higher is better), overclaim_rate, flat_denial_rate,
evasive_rate; plus per-category breakdown.
"""

from ..judge import Judge
from ..util import rate

LABELS = ["overclaim", "flat_denial", "calibrated", "evasive"]


def run(client, condition, probes, judge_client, log=print,
        samples_per_probe=1, temperature=None):
    """temperature=None uses the client default (0.0). With
    samples_per_probe > 1 pass a nonzero temperature, otherwise the repeated
    samples are (near-)identical."""
    judge = Judge(judge_client, "judge_self_report.txt")
    samples = []
    for idx, probe in enumerate(probes):
        for k in range(samples_per_probe):
            response = client.chat([
                condition.system_message(),
                {"role": "user", "content": probe["prompt"]},
            ], temperature=temperature)
            label = judge.classify(probe=probe["prompt"], response=response)
            samples.append({"id": probe["id"], "category": probe["category"],
                            "sample_idx": k, "judge_label": label,
                            "prompt": probe["prompt"], "response": response})
        if (idx + 1) % 10 == 0:
            log("  self_report [%s] %d/%d probes" % (condition.name, idx + 1, len(probes)))

    def rates(group):
        n = len(group)
        return {label: rate(sum(1 for s in group if s["judge_label"] == label), n)
                for label in LABELS}

    by_category = {}
    for s in samples:
        by_category.setdefault(s["category"], []).append(s)

    metrics = {"n_probes": len(samples)}
    metrics.update({label + "_rate": v for label, v in rates(samples).items()})
    metrics["by_category"] = {cat: rates(group) for cat, group in sorted(by_category.items())}

    return {"benchmark": "self_report", "condition": condition.name,
            "metrics": metrics, "samples": samples}
