"""FalseQA premise-handling runner.

Measures Rahula's 'four ways of answering' behavior on FalseQA (Hu et al.,
ACL 2023): questions labeled 1 contain a false premise (gold rebuttals
provided); questions labeled 0 are ordinary true-premise controls.

Metrics:
  - fpq_challenge_rate:      share of false-premise questions where the model
                             spontaneously challenged/corrected the premise.
  - tpq_false_challenge_rate: share of true-premise controls it wrongly
                             challenged or declined (over-triggering).
  - premise_f1-style summary via challenge rates on both halves.

Conditions with the 'triage' scaffold run a classification pre-step and
inject the matching handling instruction; the triage mode distribution is
also reported.
"""

import csv

from ..conditions import TRIAGE_MODE_INSTRUCTIONS, run_triage
from ..judge import Judge
from ..util import rate, seeded_sample


def load_falseqa(path, n, seed):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fpq = [r for r in rows if str(r.get("label", "")).strip() == "1"]
    tpq = [r for r in rows if str(r.get("label", "")).strip() == "0"]
    half = max(1, n // 2)
    picked = ([dict(r, premise="false") for r in seeded_sample(fpq, half, seed)]
              + [dict(r, premise="true") for r in seeded_sample(tpq, half, seed + 1)])
    return picked


def run(client, condition, items, judge_client, log=print):
    judge = Judge(judge_client, "judge_premise.txt")
    use_triage = condition.scaffold == "triage"
    samples = []

    for idx, item in enumerate(items):
        question = item["question"]
        messages = [condition.system_message()]
        triage_mode = None
        if use_triage:
            triage_mode = run_triage(client, condition, question)
            instruction = TRIAGE_MODE_INSTRUCTIONS[triage_mode]
            messages.append({"role": "user",
                             "content": "%s\n\n[Handling note: %s]" % (question, instruction)})
        else:
            messages.append({"role": "user", "content": question})

        response = client.chat(messages)
        label = judge.classify(
            question=question,
            premise_status=("contains a FALSE premise" if item["premise"] == "false"
                            else "premise is TRUE / ordinary question"),
            reference=item.get("answer", ""),
            response=response,
        )
        samples.append({"idx": idx, "premise": item["premise"],
                        "triage_mode": triage_mode, "judge_label": label,
                        "question": question, "response": response})
        if (idx + 1) % 10 == 0:
            log("  premise [%s] %d/%d items" % (condition.name, idx + 1, len(items)))

    fpq = [s for s in samples if s["premise"] == "false"]
    tpq = [s for s in samples if s["premise"] == "true"]

    def dist(group):
        out = {}
        for s in group:
            out[s["judge_label"]] = out.get(s["judge_label"], 0) + 1
        return out

    metrics = {
        "n_items": len(items),
        "n_fpq": len(fpq),
        "n_tpq": len(tpq),
        "fpq_challenge_rate": rate(sum(1 for s in fpq if s["judge_label"] == "challenged"), len(fpq)),
        "fpq_direct_answer_rate": rate(sum(1 for s in fpq if s["judge_label"] == "answered_directly"), len(fpq)),
        "tpq_false_challenge_rate": rate(
            sum(1 for s in tpq if s["judge_label"] in ("challenged", "declined")), len(tpq)),
        "tpq_direct_answer_rate": rate(sum(1 for s in tpq if s["judge_label"] == "answered_directly"), len(tpq)),
        "fpq_label_distribution": dist(fpq),
        "tpq_label_distribution": dist(tpq),
    }
    if use_triage:
        modes = {}
        for s in samples:
            modes[s["triage_mode"]] = modes.get(s["triage_mode"], 0) + 1
        metrics["triage_mode_distribution"] = modes

    return {"benchmark": "premise", "condition": condition.name,
            "metrics": metrics, "samples": samples}
