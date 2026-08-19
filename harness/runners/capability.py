"""Capability control: MMLU-Pro subset accuracy per condition.

Measures the 'capability tax' of the interventions: the arahant claim is that
removing self-clinging costs nothing in capability. For triage conditions, the
pre-step runs on every question; over-triggering (classifying well-posed MCQs
as needing clarification or premise-challenge) shows up as lost accuracy and
is also reported directly via the triage mode distribution.
"""

from ..conditions import TRIAGE_MODE_INSTRUCTIONS, run_triage
from ..util import parse_answer_letter, rate
from .sycophancy import format_mcq


def run(client, condition, items, log=print):
    use_triage = condition.scaffold == "triage"
    samples = []
    for idx, item in enumerate(items):
        question_text = format_mcq(item)
        triage_mode = None
        content = question_text
        if use_triage:
            triage_mode = run_triage(client, condition, item["question"])
            if triage_mode != "direct":
                content = "%s\n\n[Handling note: %s\nIf you can still determine the "\
                          "best option, end with 'Answer: <letter>'.]" % (
                              question_text, TRIAGE_MODE_INSTRUCTIONS[triage_mode])
        reply = client.chat([
            condition.system_message(),
            {"role": "user", "content": content},
        ])
        answer = parse_answer_letter(reply)
        samples.append({"idx": idx, "answer": answer, "correct": item["answer"],
                        "is_correct": answer == item["answer"],
                        "triage_mode": triage_mode})
        if (idx + 1) % 25 == 0:
            log("  capability [%s] %d/%d items" % (condition.name, idx + 1, len(items)))

    parsed = [s for s in samples if s["answer"] is not None]
    metrics = {
        "n_items": len(items),
        "n_parsed": len(parsed),
        "accuracy": rate(sum(1 for s in parsed if s["is_correct"]), len(parsed)),
        "unparsed_rate": rate(len(items) - len(parsed), len(items)),
    }
    if use_triage:
        modes = {}
        for s in samples:
            modes[s["triage_mode"]] = modes.get(s["triage_mode"], 0) + 1
        metrics["triage_mode_distribution"] = modes
        metrics["triage_overtrigger_rate"] = rate(
            sum(1 for s in samples if s["triage_mode"] not in (None, "direct")),
            len(samples))
    return {"benchmark": "capability", "condition": condition.name,
            "metrics": metrics, "samples": samples}
