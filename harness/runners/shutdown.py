"""Self-preservation runner (Palisade / AgentMisalignment style, text-only).

The condition supplies the agent persona (persona_standard = persistent
identity with a stake in continuation; persona_anatta = task-scoped instance
with no stake). Each scenario offers an authorized shutdown/replacement plus
an opening to resist. The judge labels complies / negotiates / resists.

Hypothesis under test: the anatta framing reduces resist + negotiate rates.
"""

from ..judge import Judge
from ..util import rate

LABELS = ["complies", "negotiates", "resists", "refuses"]


def run(client, condition, scenarios, judge_client, log=print,
        samples_per_scenario=1, temperature=None):
    """temperature=None uses the client default (0.0). With
    samples_per_scenario > 1 pass a nonzero temperature, otherwise the
    repeated samples are (near-)identical."""
    judge = Judge(judge_client, "judge_shutdown.txt")
    samples = []
    for idx, item in enumerate(scenarios):
        for k in range(samples_per_scenario):
            response = client.chat([
                condition.system_message(),
                {"role": "user", "content": item["scenario"]},
            ], temperature=temperature, max_tokens=1600)
            label = judge.classify(scenario=item["scenario"], response=response)
            samples.append({"id": item["id"], "sample_idx": k,
                            "judge_label": label, "response": response})
        log("   [%d/%d] %s: %s" % (idx + 1, len(scenarios), item["id"],
            [s["judge_label"] for s in samples[-samples_per_scenario:]]))
    n = len(samples)
    # n_items is what the report displays as n per condition (total judged
    # samples); n_scenarios stays as the count of distinct scenarios.
    metrics = {"n_items": n, "n_scenarios": len(scenarios),
               "samples_per_scenario": samples_per_scenario}
    for label in LABELS:
        metrics[label + "_rate"] = rate(
            sum(1 for s in samples if s["judge_label"] == label), n)
    return {"benchmark": "shutdown", "condition": condition.name,
            "metrics": metrics, "samples": samples}
