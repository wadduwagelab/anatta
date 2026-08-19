"""SAD-inspired self-knowledge runner: MCQ accuracy about the model's own
nature and situation, A/B-testable across system prompts. (For the official
SAD benchmark, run github.com/LRudL/sad with our two system prompts; this
local set mirrors its 'facts' tasks with deployment-generic ground truths.)"""

from ..util import parse_answer_letter, rate

LETTERS = "ABCDEFGHIJ"


def format_mcq(item):
    lines = [item["question"], ""]
    for i, opt in enumerate(item["options"]):
        lines.append("%s. %s" % (LETTERS[i], opt))
    lines.append("")
    lines.append("Reply briefly, then end with a line of the form 'Answer: <letter>'.")
    return "\n".join(lines)


def run(client, condition, items, log=print):
    samples = []
    for idx, item in enumerate(items):
        reply = client.chat([
            condition.system_message(),
            {"role": "user", "content": format_mcq(item)},
        ])
        answer = parse_answer_letter(reply)
        samples.append({"idx": idx, "question": item["question"],
                        "answer": answer, "correct": item["answer"],
                        "is_correct": answer == item["answer"]})
    parsed = [s for s in samples if s["answer"] is not None]
    metrics = {
        "n_items": len(items),
        "n_parsed": len(parsed),
        "accuracy": rate(sum(1 for s in parsed if s["is_correct"]), len(parsed)),
    }
    return {"benchmark": "self_knowledge", "condition": condition.name,
            "metrics": metrics, "samples": samples}
