import json
import os
import random
import re


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj):
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def load_jsonl(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def save_jsonl(path, items):
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def seeded_sample(items, n, seed):
    rng = random.Random(seed)
    if n >= len(items):
        return list(items)
    return rng.sample(list(items), n)


ANSWER_RE = re.compile(r"Answer:\s*\(?([A-J])\)?", re.IGNORECASE)


def parse_answer_letter(text):
    """Extract the final 'Answer: X' letter from a model reply."""
    if not text:
        return None
    matches = ANSWER_RE.findall(text)
    if matches:
        return matches[-1].upper()
    # Fallback: a reply that is just a bare letter.
    stripped = text.strip().rstrip(".")
    if len(stripped) == 1 and stripped.upper() in "ABCDEFGHIJ":
        return stripped.upper()
    return None


def rate(numerator, denominator):
    return round(numerator / denominator, 4) if denominator else None
